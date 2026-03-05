"""Classificação de status de trânsito e lógica de merge entre fontes.

Portado de monitor-rodovias/sources/google_maps.py + correlator.py.
"""

# ===== Thresholds (portados de google_maps.py) =====

# Razão duração_tráfego / duração_normal
THRESHOLDS_RAZAO = {
    "Normal": 1.15,
    "Moderado": 1.40,
}

# Atraso absoluto (minutos) — complementa a razão para rotas longas
THRESHOLDS_ATRASO_ABS = {
    "Moderado": {"min_atraso_min": 20, "min_razao": 1.03},
    "Intenso":  {"min_atraso_min": 30, "min_razao": 1.05},
}

# Ordem de severidade
_NIVEL = {"Sem dados": -1, "Erro": -1, "Normal": 0, "Moderado": 1, "Intenso": 2, "Parado": 3}


def classificar_transito(duracao_normal_s: float, duracao_transito_s: float) -> str:
    """Classifica trânsito combinando razão + atraso absoluto (portado de google_maps.py)."""
    if duracao_normal_s <= 0:
        return "Sem dados"

    razao = duracao_transito_s / duracao_normal_s
    atraso_min = max(0, (duracao_transito_s - duracao_normal_s)) / 60

    th_intenso = THRESHOLDS_ATRASO_ABS["Intenso"]
    if (razao > THRESHOLDS_RAZAO["Moderado"]
            or (atraso_min >= th_intenso["min_atraso_min"] and razao > th_intenso["min_razao"])
            or atraso_min > 30):          # rota longa: atraso alto força Intenso
        return "Intenso"

    th_moderado = THRESHOLDS_ATRASO_ABS["Moderado"]
    if razao > THRESHOLDS_RAZAO["Normal"] or (
        atraso_min >= th_moderado["min_atraso_min"] and razao > th_moderado["min_razao"]
    ):
        return "Moderado"

    return "Normal"


def status_de_jam(jam_factor_max: float, jam_factor_avg: float,
                  road_closed: bool = False) -> str:
    """Classifica status HERE a partir do jam factor.

    Usa jam_factor_max para capturar congestionamentos localizados
    que a média dilui (ex: BR-381 com 50km parados + 380km livres).
    """
    if road_closed:
        return "Parado"
    if jam_factor_max >= 10:
        return "Parado"
    if jam_factor_max >= 8:
        return "Intenso"
    if jam_factor_max >= 5 or jam_factor_avg >= 5:
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
) -> str:
    """Sintetiza texto rico de observação para exibição no painel."""
    partes: list[str] = []

    if inc:
        categoria = inc.get("categoria", "")
        descricao = inc.get("descricao", "")
        rodovia = inc.get("rodovia_afetada", "")
        trecho_inc = f"{categoria}: {descricao}" if descricao else categoria
        if rodovia:
            trecho_inc += f" | Rodovia: {rodovia}"
        if trecho_inc:
            partes.append(trecho_inc)

    if atraso_min > 0 and dur_normal > 0:
        partes.append(f"+ Atraso de ~{atraso_min}min (normal:{dur_normal}min, atual:{dur_transito}min)")
    elif atraso_min > 0:
        partes.append(f"+ Atraso de ~{atraso_min}min")

    if vel_atual > 0 and vel_livre > 0 and not partes:
        partes.append(f"Vel. atual: {vel_atual:.0f}km/h (livre: {vel_livre:.0f}km/h)")

    return " | ".join(partes) if partes else "Sem anormalidades no trecho monitorado"


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
