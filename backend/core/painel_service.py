"""Serviço de painel agregado.

Responsável por orquestrar a consulta das 20 rotas corporativas
e converter os resultados detalhados para o contrato agregado do painel.
"""

import asyncio
import logging
from datetime import datetime, timezone

from core import consultor, rotas_corporativas
from core.cache import get_cache
from core.status import inferir_ocorrencia, aplicar_override_ocorrencia, gerar_observacao, CATEGORIAS_GRAVES
from storage.repository import salvar_snapshot_agregado

logger = logging.getLogger(__name__)

_CACHE_KEY_PAINEL = "__painel_rotas_corporativas__"


def _safe_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def converter_para_resumo_painel(rota_corp: dict, resultado_detalhado: dict) -> dict:
    """Converte um ResultadoRota (detalhado) no contrato PainelRotasResponse (linha)."""
    
    # Extrair campos solicitados no contrato
    rota_id = rota_corp.get("id", "?")
    hub_o = rota_corp.get("hub_origem", "")
    hub_d = rota_corp.get("hub_destino", "")
    rodovia_logica = rota_corp.get("rodovia_logica", [])
    
    # Montar sigla, nome e trecho conforme o contrato
    sigla = " / ".join(rodovia_logica) if rodovia_logica else "Desconhecida"
    nome = f"{hub_o} -> {hub_d}"
    trecho = f"{hub_o} / {hub_d}"
    
    status_base = resultado_detalhado.get("status", "Erro")

    incidente_dict = resultado_detalhado.get("incidente_principal") or {}
    jam_max = resultado_detalhado.get("jam_factor_max", 0) or 0
    atraso_min_raw = resultado_detalhado.get("atraso_min", 0)
    try:
        atraso_min = int(atraso_min_raw)
    except (ValueError, TypeError):
        atraso_min = 0

    ocorrencia = inferir_ocorrencia(
        incidente_dict if incidente_dict else None,
        float(jam_max),
        atraso_min,
    )
    status = aplicar_override_ocorrencia(status_base, ocorrencia, float(jam_max), atraso_min)

    relato = gerar_observacao(
        inc=incidente_dict if incidente_dict else None,
        atraso_min=atraso_min,
        dur_normal=_safe_int(resultado_detalhado.get("duracao_normal_min", 0)),
        dur_transito=_safe_int(resultado_detalhado.get("duracao_transito_min", 0)),
        pct_cong=float(resultado_detalhado.get("pct_congestionado", 0) or 0),
        jam_avg=float(resultado_detalhado.get("jam_factor_avg", 0) or 0),
        vel_atual=float(resultado_detalhado.get("velocidade_atual_kmh", 0) or 0),
        vel_livre=float(resultado_detalhado.get("velocidade_livre_kmh", 0) or 0),
        sigla=sigla,
        hub_origem=hub_o,
        hub_destino=hub_d,
        incidentes=resultado_detalhado.get("incidentes", []),
        status_google=resultado_detalhado.get("status_google", ""),
        status_here=resultado_detalhado.get("status_here", ""),
    )

    hora_atualizacao = resultado_detalhado.get("consultado_em", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))

    # Tratar confianca se for string (e.g., "?")
    confianca_pct_raw = resultado_detalhado.get("confianca_pct", 0)
    try:
        confianca_pct = int(confianca_pct_raw)
    except (ValueError, TypeError):
        confianca_pct = 0

    return {
        "rota_id": rota_id,
        "sigla": sigla,
        "nome": nome,
        "trecho": trecho,
        "status": status,
        "ocorrencia": ocorrencia,
        "ocorrencia_principal": ocorrencia,
        "relato": relato,
        "observacao_resumo": relato,
        "hora_atualizacao": hora_atualizacao,
        "confianca_pct": confianca_pct,
        "atraso_min": atraso_min,
        "duracao_normal_min": resultado_detalhado.get("duracao_normal_min", 0),
        "duracao_transito_min": resultado_detalhado.get("duracao_transito_min", 0),
        "jam_factor_max": resultado_detalhado.get("jam_factor_max", 0),
        "distancia_km": resultado_detalhado.get("distancia_km", 0),
        "link_waze": resultado_detalhado.get("link_waze", ""),
        "link_gmaps": resultado_detalhado.get("link_gmaps", ""),
        "incidentes": resultado_detalhado.get("incidentes", []),
    }


async def obter_painel_agregado(config: dict) -> dict:
    """Retorna o painel agregado puxando direto do ultimo ciclo salvo no Supabase."""
    from storage.database import get_supabase
    
    rotas = rotas_corporativas.carregar_rotas(config)
    def_vazio = {
        "consultado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fonte": "cache_banco",
        "total_rotas": 0,
        "resultados": []
    }
    
    if not rotas:
        return def_vazio

    client = get_supabase()
    if not client:
        logger.warning("Supabase não configurado. Retornando vazio.")
        return def_vazio

    try:
        # 1. Busca o último ciclo
        resp_ciclo = client.get("/ciclos?order=ts_iso.desc&limit=1")
        resp_ciclo.raise_for_status()
        dados = resp_ciclo.json()

        if not dados:
            return def_vazio

        ultimo_ciclo = dados[0]
        ciclo_id = ultimo_ciclo.get("id")

        # 2. Busca os snapshots do ciclo separadamente (evita dependência de FK no PostgREST)
        resp_snaps = client.get(f"/snapshots_rotas?ciclo_id=eq.{ciclo_id}")
        resp_snaps.raise_for_status()
        snapshots = resp_snaps.json()
        
        # Mapeia os snapshots pelas siglas/trechos
        mapa_snapshots = {}
        for snap in snapshots:
            # Assumimos que a identificação clara possa ser a sigla ou o trecho original
            # Na falta de um ID, usamos a Rodovia e o Trecho para cruzar The map
            chave = f"{snap.get('rodovia')}::{snap.get('trecho')}"
            mapa_snapshots[chave] = snap
            
        linhas_painel = []
        for r in rotas:
            rota_id = r.get("id", "?")
            hub_o = r.get("hub_origem", "")
            hub_d = r.get("hub_destino", "")
            rodovia_logica = r.get("rodovia_logica", [])
            
            sigla = " / ".join(rodovia_logica) if rodovia_logica else "Desconhecida"
            nome = f"{hub_o} -> {hub_d}"
            trecho = f"{hub_o} / {hub_d}"
            
            chave = f"{sigla}::{trecho}"
            snap = mapa_snapshots.get(chave)
            
            if snap:
                status = snap.get("status", "N/A")
                ocorrencia = snap.get("ocorrencia_principal") or snap.get("ocorrencia", "")
                relato = snap.get("observacao_resumo") or snap.get("descricao", "")
                hora_atualizacao = snap.get("ts_iso", "")
                confianca_pct = snap.get("confianca_pct", 0)
                atraso_min = snap.get("atraso_min", 0)
                try:
                    _atr = int(atraso_min) if atraso_min is not None else 0
                except (ValueError, TypeError):
                    _atr = 0
                # Regra de supressão: atraso medido pelo Google < 20 min → Normal.
                # Isenção: incidentes graves mantêm status mesmo com atraso baixo.
                if 0 < _atr < 20 and status in ("Moderado", "Intenso"):
                    if ocorrencia not in CATEGORIAS_GRAVES:
                        status = "Normal"
            else:
                status = "N/A"
                ocorrencia = ""
                relato = "Sem dados no ultimo ciclo"
                hora_atualizacao = ultimo_ciclo.get("ts_iso", "")
                confianca_pct = 0
                atraso_min = 0

            linhas_painel.append({
                "rota_id": rota_id,
                "sigla": sigla,
                "nome": nome,
                "trecho": trecho,
                "status": status,
                "ocorrencia": ocorrencia,
                "ocorrencia_principal": ocorrencia,
                "relato": relato,
                "observacao_resumo": relato,
                "hora_atualizacao": hora_atualizacao,
                "confianca_pct": confianca_pct,
                "atraso_min": atraso_min,
                "duracao_normal_min": (snap.get("duracao_normal_min") or 0) if snap else 0,
                "duracao_transito_min": (snap.get("duracao_transito_min") or 0) if snap else 0,
                "jam_factor_max": (snap.get("jam_factor_max") or 0) if snap else 0,
                "distancia_km": r.get("distance_km", 0),
                "incidentes": [],  # incidentes não são persistidos no snapshot
                "dados_origem": "snapshot",
            })

        return {
            "consultado_em": ultimo_ciclo.get("ts_iso", ""),
            "fonte": "supabase",
            "dados_origem": "snapshot",
            "ciclo_id": ciclo_id,
            "total_rotas": len(linhas_painel),
            "resultados": linhas_painel,
        }

    except Exception as e:
        logger.error(f"Erro ao buscar painel do Supabase: {e}")
        return def_vazio
