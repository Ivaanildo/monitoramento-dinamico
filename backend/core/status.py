"""Classificação de status de trânsito e lógica de merge entre fontes.

Portado de monitor-rodovias/sources/google_maps.py + correlator.py.
"""

# Ordem de severidade
_NIVEL = {"Sem dados": -1, "Erro": -1, "Normal": 0, "Moderado": 1, "Intenso": 2, "Parado": 3}


def classificar_transito(duracao_normal_s: float, duracao_transito_s: float) -> str:
    """Classifica trânsito baseado no atraso absoluto em minutos.

    Faixas: 0-20 min → Normal | >20-30 min → Moderado | >=30 min → Intenso
    """
    if duracao_normal_s <= 0:
        return "Sem dados"

    atraso_min = max(0, (duracao_transito_s - duracao_normal_s)) / 60

    if atraso_min >= 30:
        return "Intenso"
    if atraso_min > 20:
        return "Moderado"
    return "Normal"


def status_de_jam(jam_factor_max: float, jam_factor_avg: float,
                  road_closed: bool = False, pct_cong: float = 0) -> str:
    """Classifica status HERE a partir do jam factor.

    Usa jam_factor_max para capturar congestionamentos localizados
    que a média dilui (ex: BR-381 com 50km parados + 380km livres).
    Requer pct_cong >= 15 para promover a Intenso e pct_cong >= 10 para
    promover a Moderado (evita falsos positivos por segmentos isolados).
    """
    if road_closed:
        return "Parado"
    if jam_factor_max >= 10:
        return "Parado"
    if jam_factor_max >= 8 and pct_cong >= 15:
        return "Intenso"
    if (jam_factor_max >= 5 or jam_factor_avg >= 5) and pct_cong >= 10:
        return "Moderado"
    return "Normal"


def mais_severo(s1: str, s2: str) -> str:
    """Retorna o status mais severo entre dois."""
    n1 = _NIVEL.get(s1, -1)
    n2 = _NIVEL.get(s2, -1)
    return s1 if n1 >= n2 else s2


def status_final(google_status: str, here_status: str) -> str:
    """Merge de status: o mais severo entre Google e HERE vence."""
    return mais_severo(google_status, here_status)


def calcular_confianca(google_ok: bool, here_ok: bool, atraso_min: int) -> tuple[str, int]:
    """Calcula confiança textual e percentual baseado nas fontes disponíveis.

    Returns:
        (texto, percentual) — ex: ("Alta", 100)
    """
    if google_ok and here_ok:
        return "Alta", 100
    elif google_ok or here_ok:
        return "Média", 50
    else:
        return "Baixa", 0


def incidente_principal(incidentes: list) -> dict | None:
    """Retorna o dict do incidente mais grave da lista HERE, ou None."""
    if not incidentes:
        return None
    pesos = {
        "Interdição": 5,
        "Bloqueio Parcial": 4,
        "Colisão": 3,
        "Obras na Pista": 2,
        "Engarrafamento": 1,
        "Condição Climática": 1,
        "Ocorrência": 0,
    }
    return max(incidentes, key=lambda i: pesos.get(i.get("categoria", ""), 0))


def gerar_observacao(
    inc: dict | None,
    atraso_min: int,
    dur_normal: int,
    dur_transito: int,
    pct_cong: float,
    jam_avg: float,
    vel_atual: float,
    vel_livre: float,
    sigla: str = "",
    hub_origem: str = "",
    hub_destino: str = "",
) -> str:
    """Sintetiza texto operacional de observação para exibição no painel e Excel."""
    via = sigla or "trecho monitorado"

    if atraso_min > 0:
        categoria = ""
        if inc:
            categoria = inc.get("categoria", "")
        if not categoria:
            categoria = "Engarrafamento"
        return (
            f"{categoria} (Google Maps) em {via}: "
            f"Atraso {atraso_min} min | "
            f"Atraso estimado: {atraso_min} min | "
            f"Google: lentidao no trecho inicial"
        )

    # Sem atraso mas com incidente HERE (ex: obras noturnas sem impacto ainda)
    if inc:
        categoria = inc.get("categoria", "Ocorrência")
        descricao = inc.get("descricao", "")
        rodovia = inc.get("rodovia_afetada", "")
        partes = [f"{categoria} em {via}"]
        if descricao:
            partes.append(descricao)
        if rodovia:
            partes.append(f"Rodovia: {rodovia}")
        return " | ".join(partes) + " | Sem impacto no tempo de viagem no momento"

    if hub_origem and hub_destino:
        return f"Via {via}, sentido {hub_origem} -> {hub_destino} sem anormalidades, fluxo livre."

    return f"Via {via} sem anormalidades, fluxo livre."


def inferir_ocorrencia(incidente_principal: dict | None, jam_max: float, atraso_min: int) -> str:
    """Retorna categoria de ocorrência, inferindo Engarrafamento se necessário."""
    if incidente_principal:
        return incidente_principal.get("categoria", "")
    if jam_max >= 5 or atraso_min >= 20:
        return "Engarrafamento"
    return ""


def aplicar_override_ocorrencia(status_base: str, ocorrencia_tipo: str,
                                 jam_max: float = 0, atraso_min: int = 0) -> str:
    """Eleva status conforme o tipo de ocorrência detectada."""
    if ocorrencia_tipo == "Interdição":
        return mais_severo(status_base, "Parado")
    if ocorrencia_tipo in ("Colisão", "Acidente"):
        return mais_severo(status_base, "Intenso")
    if ocorrencia_tipo == "Bloqueio Parcial":
        return mais_severo(status_base, "Moderado")
    return status_base
