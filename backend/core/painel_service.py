"""Serviço de painel agregado.

Responsável por orquestrar a consulta das 20 rotas corporativas
e converter os resultados detalhados para o contrato agregado do painel.
"""

import asyncio
import logging
from datetime import datetime, timezone

from core import consultor, rotas_corporativas
from core.cache import get_cache
from storage.repository import salvar_snapshot_agregado

logger = logging.getLogger(__name__)

_CACHE_KEY_PAINEL = "__painel_rotas_corporativas__"


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
    
    status = resultado_detalhado.get("status", "Erro")
    
    incidente_dict = resultado_detalhado.get("incidente_principal") or {}
    ocorrencia = incidente_dict.get("categoria", "") if incidente_dict else ""
    relato = resultado_detalhado.get("relato") or (incidente_dict.get("descricao", "") if incidente_dict else "")
    
    hora_atualizacao = resultado_detalhado.get("consultado_em", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    
    # Tratar confianca se for string (e.g., "?")
    confianca_pct_raw = resultado_detalhado.get("confianca_pct", 0)
    try:
        confianca_pct = int(confianca_pct_raw)
    except (ValueError, TypeError):
        confianca_pct = 0
        
    atraso_min = resultado_detalhado.get("atraso_min", 0)

    return {
        "rota_id": rota_id,
        "sigla": sigla,
        "nome": nome,
        "trecho": trecho,
        "status": status,
        "ocorrencia": ocorrencia,
        "relato": relato,
        "hora_atualizacao": hora_atualizacao,
        "confianca_pct": confianca_pct,
        "atraso_min": atraso_min,
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
                ocorrencia = snap.get("ocorrencia", "")
                relato = snap.get("descricao", "")
                hora_atualizacao = snap.get("ts_iso", "")
                confianca_pct = snap.get("confianca_pct", 0)
                atraso_min = snap.get("atraso_min", 0)
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
                "relato": relato,
                "hora_atualizacao": hora_atualizacao,
                "confianca_pct": confianca_pct,
                "atraso_min": atraso_min,
                "distancia_km": r.get("distance_km", 0)
            })

        return {
            "consultado_em": ultimo_ciclo.get("ts_iso", ""),
            "fonte": "supabase",
            "total_rotas": len(linhas_painel),
            "resultados": linhas_painel
        }

    except Exception as e:
        logger.error(f"Erro ao buscar painel do Supabase: {e}")
        return def_vazio
