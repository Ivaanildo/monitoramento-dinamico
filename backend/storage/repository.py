"""Repository layer for Supabase persistence.

Saves analytical snapshots without blocking the primary request flow.
"""
import logging
from datetime import datetime, timezone
import httpx
from storage.database import get_supabase

logger = logging.getLogger(__name__)

def salvar_snapshot_agregado(resultados: list, font_list: str = "google,here"):
    """Salva os resultados consolidados do painel em `ciclos` e `snapshots_rotas`.
    
    Falhas aqui nao propagam exceção para evitar downtime na API de leitura.
    """
    client = get_supabase()
    if not client:
        return  # Supabase não configurado

    try:
        agora_iso = datetime.now(timezone.utc).isoformat()
        
        # 1. Cria o Ciclo via REST
        res_ciclo = client.post("/ciclos", json={
            "ts": agora_iso,
            "ts_iso": agora_iso,
            "fontes": font_list
        })
        res_ciclo.raise_for_status()
        
        data_ciclo = res_ciclo.json()
        if not data_ciclo or not isinstance(data_ciclo, list):
            logger.error(f"Falha ao criar ciclo no Supabase: Resposta inesperada {data_ciclo}")
            return

        ciclo_id = data_ciclo[0]["id"]
        
        # 2. Prepara e insere os snapshots
        registros = []
        for r in resultados:
            ocorrencia = r.get("ocorrencia_principal") or r.get("ocorrencia", "")
            observacao = r.get("observacao_resumo") or r.get("relato", "")
            registros.append({
                "ciclo_id": ciclo_id,
                "rota_id": r.get("rota_id", ""),
                "trecho": r.get("trecho", ""),
                "rodovia": r.get("sigla", ""),
                "status": r.get("status", "Normal"),
                "ocorrencia": ocorrencia,
                "ocorrencia_principal": ocorrencia,
                "descricao": observacao,
                "observacao_resumo": observacao,
                "atraso_min": r.get("atraso_min", 0),
                "confianca_pct": r.get("confianca_pct", 0),
                "conflito_fontes": 0,
                "ts_iso": agora_iso,
            })

        if registros:
            res_snaps = client.post("/snapshots_rotas", json=registros)
            res_snaps.raise_for_status()
        
        logger.info(f"Snapshot agregado salvo com sucesso: Ciclo {ciclo_id} com {len(registros)} rotas.")

    except httpx.HTTPStatusError as e:
        logger.error(f"Erro HTTP {e.response.status_code} ao persisitir no Supabase: {e.response.text}")
    except Exception as e:
        logger.error(f"Erro silencioso ao persisitir no Supabase: {e}")
