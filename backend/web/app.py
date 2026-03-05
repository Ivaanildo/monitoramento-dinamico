"""FastAPI server — Projeto Zero.

Endpoints:
  GET  /                          → index.html
  GET  /consultar?origem=&destino=→ JSON ResultadoRota
  GET  /exportar/excel            → download .xlsx
  GET  /exportar/csv              → download .csv
  GET  /favoritos                 → lista do favoritos.json
  POST /favoritos                 → salva nova rota favorita
  GET  /cache/info                → info do cache (size, ttl)
  DELETE /cache                   → limpa o cache
"""
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone

_BRT = timezone(timedelta(hours=-3))
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Depends, Response
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core import consultor, rotas_corporativas, painel_service, auth_local
from core.cache import get_cache
from core.config_loader import load_config
from core.logging_setup import setup_logging
from report.excel_simple import gerar_csv, gerar_excel, gerar_csv_visao_geral, gerar_excel_visao_geral
from storage import database

setup_logging()
logger = logging.getLogger(__name__)

# ===== Configuração injetada externamente =====
_config: dict = {}

_BASE = Path(__file__).parent
_FAVORITOS_PATH = _BASE.parent / "data" / "favoritos.json"
_STATIC_PATH = _BASE / "static"

app = FastAPI(
    title="Projeto Zero — Consulta de Rotas On-Demand",
    version="1.0.0",
    description="Consulta tráfego em tempo real: Google Routes API v2 + HERE Traffic",
)

# Monta arquivos estáticos
if _STATIC_PATH.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_PATH)), name="static")

@app.on_event("startup")
async def startup_event():
    """Inicializa configurações e o cliente Supabase no startup do Uvicorn."""
    global _config
    if not _config:
        config_path = _BASE.parent / "config.yaml"
        try:
            _config = load_config(config_path)
            if logger.isEnabledFor(logging.INFO):
                logger.info("Configuração carregada no startup do Uvicorn.")
        except Exception as e:
            logger.error(f"Erro ao carregar {config_path}: {e}")
    database.init_supabase(_config)


# ===== Modelos =====

class FavoritoIn(BaseModel):
    nome: str
    origem: str
    destino: str


class LoginIn(BaseModel):
    username: str
    password: str


def verificar_autenticacao(request: Request):
    """Dependencia para rotas protegidas."""
    return auth_local.validar_sessao(request, _config)


@app.get("/healthz")
async def healthz():
    """Health check publico para deploys e monitoramento."""
    return JSONResponse(content={"status": "ok"})


# ===== Helpers =====

def _carregar_favoritos() -> list:
    """Retorna apenas os favoritos definidos pelo usuário."""
    try:
        if _FAVORITOS_PATH.exists():
            with open(_FAVORITOS_PATH, encoding="utf-8") as f:
                return json.load(f).get("favoritos", [])
    except Exception as e:
        logger.warning(f"Erro ao carregar favoritos: {e}")
    return []


def _carregar_rotas_predefinidas() -> list:
    """Converte as rotas do favoritos.json para o formato de favorito."""
    try:
        if _FAVORITOS_PATH.exists():
            with open(_FAVORITOS_PATH, encoding="utf-8") as f:
                dados = json.load(f)
            resultado = []
            for r in dados.get("routes", []):
                orig = r.get("here", {}).get("origin", "")
                dest = r.get("here", {}).get("destination", "")
                hub_o = r.get("origem", {}).get("hub", orig)
                hub_d = r.get("destino", {}).get("hub", dest)
                resultado.append({
                    "nome": f"{r.get('id', '?')}: {hub_o} → {hub_d}",
                    "origem": orig,
                    "destino": dest,
                    "via": r.get("here", {}).get("via", []),
                    "rodovia_logica": r.get("rodovia_logica", []),
                    "predefinida": True,
                })
            return resultado
    except Exception as e:
        logger.warning(f"Erro ao carregar rotas predefinidas: {e}")
    return []


def _salvar_favoritos(lista: list) -> None:
    """Salva favoritos do usuário preservando as demais chaves do arquivo."""
    dados: dict = {}
    if _FAVORITOS_PATH.exists():
        try:
            with open(_FAVORITOS_PATH, encoding="utf-8") as f:
                dados = json.load(f)
        except Exception:
            pass
    dados["favoritos"] = lista
    with open(_FAVORITOS_PATH, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def _validar_params(origem: str, destino: str) -> None:
    if not origem or not origem.strip():
        raise HTTPException(status_code=400, detail="Parâmetro 'origem' é obrigatório")
    if not destino or not destino.strip():
        raise HTTPException(status_code=400, detail="Parâmetro 'destino' é obrigatório")
    if origem.strip() == destino.strip():
        raise HTTPException(status_code=400, detail="Origem e destino não podem ser iguais")


def _deve_ignorar_log_http(path: str) -> bool:
    return path == "/favicon.ico" or path.startswith("/static/")


def _request_id_from(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def _erro_500_payload(request_id: str) -> dict:
    return {
        "detail": "Erro interno do servidor. Consulte os logs do backend.",
        "request_id": request_id,
    }


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = uuid.uuid4().hex[:8]
    request.state.request_id = request_id

    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "-"
    ignorar_log = _deve_ignorar_log_http(path)
    inicio = time.perf_counter()

    if not ignorar_log:
        logger.info(f"[{request_id}] -> {method} {path} ip={client_ip}")

    try:
        response = await call_next(request)
    except HTTPException as exc:
        response = await http_exception_handler(request, exc)
    except Exception as exc:
        response = await unhandled_exception_handler(request, exc)
    response.headers["X-Request-ID"] = request_id

    duracao_ms = (time.perf_counter() - inicio) * 1000
    if not ignorar_log:
        status_code = response.status_code
        msg = (
            f"[{request_id}] <- {method} {path} "
            f"status={status_code} duracao_ms={duracao_ms:.1f} ip={client_ip}"
        )
        if status_code >= 500:
            logger.error(msg)
        elif status_code >= 400:
            logger.warning(msg)
        else:
            logger.info(msg)

    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = _request_id_from(request)

    if exc.status_code >= 500:
        logger.error(
            f"[{request_id}] HTTPException {exc.status_code} em "
            f"{request.method} {request.url.path}: {exc.detail}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_erro_500_payload(request_id),
            headers={**(exc.headers or {}), "X-Request-ID": request_id},
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={**(exc.headers or {}), "X-Request-ID": request_id},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = _request_id_from(request)
    logger.exception(f"[{request_id}] Erro interno em {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content=_erro_500_payload(request_id),
        headers={"X-Request-ID": request_id},
    )


# ===== Endpoints =====

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    index = _STATIC_PATH / "index.html"
    if index.exists():
        return index.read_text(encoding="utf-8")
    return "<h1>Projeto Zero</h1><p>index.html não encontrado em web/static/</p>"


@app.get("/consultar")
async def consultar_rota(
    origem: str = Query(..., description="Endereço ou 'lat,lng' de origem"),
    destino: str = Query(..., description="Endereço ou 'lat,lng' de destino"),
    via: list[str] = Query(default=[], description="Waypoints via no formato HERE"),
    rodovia_logica: list[str] = Query(default=[], description="Codigos de rodovia para filtro semantico"),
):
    """Retorna JSON com status de tráfego para a rota informada."""
    _validar_params(origem, destino)
    loop = asyncio.get_running_loop()
    resultado = await loop.run_in_executor(
        None,
        lambda: consultor.consultar(
            _config,
            origem.strip(),
            destino.strip(),
            via or None,
            rodovia_logica or None,
        ),
    )
    return JSONResponse(content=resultado)


# --- Auth Endpoints ---

@app.post("/auth/login")
async def login(credentials: LoginIn):
    """Autentica usuario local e gera cookie simples."""
    if auth_local.is_auth_blocked(_config):
        resp = JSONResponse(
            content={"detail": "Auth local bloqueada por configuracao insegura"},
            status_code=503,
        )
        auth_local.limpar_sessao(resp, _config)
        return resp

    if not auth_local.is_auth_enabled(_config):
        return JSONResponse(content={"message": "Auth local desabilitada"})

    valid_user, valid_pass = auth_local.get_credentials(_config)
    if credentials.username != valid_user or credentials.password != valid_pass:
        resp = JSONResponse(content={"detail": "Credenciais invalidas"}, status_code=401)
        auth_local.limpar_sessao(resp, _config)
        return resp

    resp = JSONResponse(content={"message": "Login efetuado com sucesso"})
    auth_local.criar_sessao(resp, valid_user, _config)
    return resp


@app.post("/auth/logout")
async def logout():
    """Limpa a sessao atual."""
    resp = JSONResponse(content={"message": "Sessao encerrada"})
    auth_local.limpar_sessao(resp, _config)
    return resp


@app.get("/auth/session")
async def check_session(request: Request):
    """Verifica se existe sessao ativa (usado pelo frontend no boot)."""
    if auth_local.is_auth_blocked(_config):
        return JSONResponse(
            content={"authenticated": False, "auth_blocked": True},
            status_code=503,
        )

    if not auth_local.is_auth_enabled(_config):
        return JSONResponse(content={"authenticated": True, "username": "operacao", "mode": "local-temp"})
        
    try:
        username = auth_local.validar_sessao(request, _config)
        return JSONResponse(content={"authenticated": True, "username": username, "mode": "local-temp"})
    except HTTPException:
        return JSONResponse(content={"authenticated": False}, status_code=401)


# --- Rotas Corporativas e Painel (Protegidos) ---

@app.get("/rotas")
async def listar_rotas_corporativas(user: str = Depends(verificar_autenticacao)):
    """Retorna as 20 rotas corporativas normalizadas."""
    rotas = rotas_corporativas.carregar_rotas(_config)
    return JSONResponse(content={"rotas": rotas})


@app.get("/rotas/{rota_id}")
async def obter_rota_corporativa(rota_id: str, user: str = Depends(verificar_autenticacao)):
    """Busca uma rota especifica por ID (R01 a R20)."""
    rota = rotas_corporativas.buscar_rota_por_id(_config, rota_id.upper())
    if not rota:
        raise HTTPException(status_code=404, detail="Rota corporativa nao encontrada")
    return JSONResponse(content=rota)


@app.get("/rotas/{rota_id}/consultar")
async def consultar_rota_corporativa(rota_id: str, user: str = Depends(verificar_autenticacao)):
    """Consulta trafego detalhado de uma rota predefinida, utilizando suas vias/codigos configurados."""
    rota = rotas_corporativas.buscar_rota_por_id(_config, rota_id.upper())
    if not rota:
        raise HTTPException(status_code=404, detail="Rota corporativa nao encontrada")
    
    kwargs = rotas_corporativas.converter_para_parametros_consulta(rota)
    
    loop = asyncio.get_running_loop()
    resultado = await loop.run_in_executor(
        None,
        lambda: consultor.consultar(
            _config,
            origem=kwargs["origem"],
            destino=kwargs["destino"],
            via=kwargs["via"] or None,
            rodovia_logica=kwargs["rodovia_logica"] or None,
        ),
    )
    # Adicionando identificadores para mapeamento frontend detalhado
    resultado["rota_id"] = rota_id.upper()
    resultado["hub_origem"] = rota.get("hub_origem")
    resultado["hub_destino"] = rota.get("hub_destino")
    
    # Montando via_coords igual o visao-geral antigo
    via_coords = []
    for v in kwargs["via"]:
        try:
            coords_str = v.split("!")[0].split(",")
            via_coords.append({"lat": float(coords_str[0]), "lng": float(coords_str[1])})
        except Exception:
            pass
    resultado["via_coords"] = via_coords

    return JSONResponse(content=resultado)


@app.get("/rotas/{rota_id}/snapshot")
async def get_snapshot_rota(rota_id: str, user: str = Depends(verificar_autenticacao)):
    """Retorna o último snapshot do ciclo periódico para a rota informada."""
    from storage.database import get_supabase
    client = get_supabase()
    if not client:
        raise HTTPException(status_code=503, detail="Banco de dados não disponível")
    try:
        resp = client.get(
            f"/snapshots_rotas?rota_id=eq.{rota_id.upper()}&order=ts_iso.desc&limit=1"
        )
        resp.raise_for_status()
        dados = resp.json()
    except Exception as e:
        logger.warning(f"Erro ao buscar snapshot para {rota_id}: {e}")
        raise HTTPException(status_code=503, detail="Erro ao consultar banco de dados")
    if not dados:
        raise HTTPException(status_code=404, detail="Snapshot não encontrado para esta rota")
    snap = dados[0]
    return JSONResponse(content={
        "rota_id": rota_id.upper(),
        "status": snap.get("status", "N/A"),
        "atraso_min": snap.get("atraso_min", 0),
        "ocorrencia_principal": snap.get("ocorrencia_principal") or snap.get("ocorrencia", ""),
        "observacao_resumo": snap.get("observacao_resumo") or snap.get("descricao", ""),
        "ciclo_ts": snap.get("ciclo_ts") or snap.get("ts_iso", ""),
        "dados_origem": "snapshot",
    })


@app.get("/painel")
async def obter_painel_agregado(user: str = Depends(verificar_autenticacao)):
    """Retorna o resumo consolidado das 20 rotas corporativas."""
    resultados = await painel_service.obter_painel_agregado(_config)
    return JSONResponse(content=resultados)


@app.get("/exportar/excel")
async def exportar_excel(
    origem: str = Query(...),
    destino: str = Query(...),
    rodovia_logica: list[str] = Query(default=[]),
):
    """Download do relatório Excel (.xlsx) para a rota informada."""
    _validar_params(origem, destino)
    loop = asyncio.get_running_loop()
    resultado = await loop.run_in_executor(
        None,
        lambda: consultor.consultar(
            _config,
            origem.strip(),
            destino.strip(),
            None,
            rodovia_logica or None,
        ),
    )
    xlsx_bytes = gerar_excel(resultado)
    nome = f"rota_{origem[:20].replace(' ', '_')}_{destino[:20].replace(' ', '_')}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@app.get("/exportar/csv")
async def exportar_csv(
    origem: str = Query(...),
    destino: str = Query(...),
    rodovia_logica: list[str] = Query(default=[]),
):
    """Download do relatório CSV para a rota informada."""
    _validar_params(origem, destino)
    loop = asyncio.get_running_loop()
    resultado = await loop.run_in_executor(
        None,
        lambda: consultor.consultar(
            _config,
            origem.strip(),
            destino.strip(),
            None,
            rodovia_logica or None,
        ),
    )
    csv_str = gerar_csv(resultado)
    nome = f"rota_{origem[:20].replace(' ', '_')}_{destino[:20].replace(' ', '_')}.csv"
    return Response(
        content=csv_str.encode("utf-8-sig"),  # BOM para Excel pt-BR
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@app.get("/favoritos")
async def listar_favoritos(user: str = Depends(verificar_autenticacao)):
    """Retorna favoritos do usuário + rotas predefinidas do favoritos.json."""
    favs = _carregar_favoritos()
    rotas = _carregar_rotas_predefinidas()
    return JSONResponse(content={"favoritos": favs + rotas})


@app.post("/favoritos", status_code=201)
async def salvar_favorito(favorito: FavoritoIn, user: str = Depends(verificar_autenticacao)):
    """Adiciona uma nova rota à lista de favoritos."""
    lista = _carregar_favoritos()

    # Evitar duplicatas pelo par origem+destino
    for f in lista:
        if (f.get("origem", "").strip().lower() == favorito.origem.strip().lower()
                and f.get("destino", "").strip().lower() == favorito.destino.strip().lower()):
            return JSONResponse(
                status_code=200,
                content={"message": "Favorito já existe", "favoritos": lista},
            )

    lista.append({
        "nome": favorito.nome.strip(),
        "origem": favorito.origem.strip(),
        "destino": favorito.destino.strip(),
    })
    _salvar_favoritos(lista)
    return JSONResponse(content={"message": "Favorito salvo", "favoritos": lista})


@app.delete("/favoritos")
async def remover_favorito(
    origem: str = Query(...),
    destino: str = Query(...),
    user: str = Depends(verificar_autenticacao),
):
    """Remove um favorito pelo par origem+destino."""
    lista = _carregar_favoritos()
    nova_lista = [
        f for f in lista
        if not (f.get("origem", "").strip().lower() == origem.strip().lower()
                and f.get("destino", "").strip().lower() == destino.strip().lower())
    ]
    _salvar_favoritos(nova_lista)
    return JSONResponse(content={"message": "Favorito removido", "favoritos": nova_lista})


@app.get("/cache/info")
async def cache_info(user: str = Depends(verificar_autenticacao)):
    """Retorna informações sobre o cache em memória."""
    ttl = int(((_config or {}).get("cache", {}) or {}).get("ttl_segundos", 300))
    cache = get_cache(ttl)
    return JSONResponse(content={
        "tamanho": cache.size(),
        "ttl_segundos": ttl,
    })


@app.delete("/cache")
async def limpar_cache(user: str = Depends(verificar_autenticacao)):
    """Limpa o cache em memória (força nova consulta às APIs)."""
    ttl = int(((_config or {}).get("cache", {}) or {}).get("ttl_segundos", 300))
    cache = get_cache(ttl)
    cache.clear()
    return JSONResponse(content={"message": "Cache limpo"})


_CACHE_KEY_VISAO_GERAL = "__visao_geral__"


async def _obter_resultados_visao_geral() -> list:
    """Retorna lista de resultados da visão geral (cache ou consulta)."""
    import asyncio

    ttl = int(((_config or {}).get("cache", {}) or {}).get("ttl_segundos", 300))
    cache = get_cache(ttl)
    cached = cache.get(_CACHE_KEY_VISAO_GERAL)
    if cached:
        logger.info("Cache hit: visao_geral")
        return cached.get("resultados", [])

    if not _FAVORITOS_PATH.exists():
        raise HTTPException(status_code=404, detail="favoritos.json não encontrado")
    try:
        with open(_FAVORITOS_PATH, encoding="utf-8") as f:
            dados = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler favoritos.json: {e}")

    routes = dados.get("routes", [])
    if not routes:
        cache.set(_CACHE_KEY_VISAO_GERAL, {"resultados": []})
        return []

    loop = asyncio.get_running_loop()

    async def _consultar_uma(r: dict) -> dict:
        orig = r.get("here", {}).get("origin", "")
        dest = r.get("here", {}).get("destination", "")
        via = r.get("here", {}).get("via", []) or []
        rodovia_logica = r.get("rodovia_logica", []) or []
        hub_o = r.get("origem", {}).get("hub", orig)
        hub_d = r.get("destino", {}).get("hub", dest)
        rota_id = r.get("id", "?")
        dist_km = r.get("waypoints_status", {}).get("distance_km", 0)
        try:
            resultado = await loop.run_in_executor(
                None, consultor.consultar, _config, orig, dest, via or None, rodovia_logica or None
            )
            resultado["rota_id"] = rota_id
            resultado["hub_origem"] = hub_o
            resultado["hub_destino"] = hub_d
            resultado["distancia_predefinida_km"] = dist_km
            via_raw = r.get("here", {}).get("via", [])
            via_coords = []
            for v in via_raw:
                try:
                    coords_str = v.split("!")[0].split(",")
                    via_coords.append({"lat": float(coords_str[0]), "lng": float(coords_str[1])})
                except Exception:
                    pass
            resultado["via_coords"] = via_coords
            return resultado
        except Exception as e:
            return {
                "rota_id": rota_id,
                "hub_origem": hub_o,
                "hub_destino": hub_d,
                "distancia_predefinida_km": dist_km,
                "status": "Erro",
                "erros": {"geral": str(e)},
            }

    resultados = list(await asyncio.gather(*[_consultar_uma(r) for r in routes]))
    cache.set(_CACHE_KEY_VISAO_GERAL, {"resultados": resultados})
    return resultados


# Os endpoints antigos de _visao_geral continuam para retrocompatibilidade técnica caso necessário, 
# mas o oficial agora é o /painel
@app.get("/visao-geral")
async def visao_geral():
    """Consulta todas as rotas predefinidas do favoritos.json em paralelo. Usa cache agregado."""
    resultados = await _obter_resultados_visao_geral()
    return JSONResponse(content={"resultados": resultados})


@app.get("/painel/exportar/excel")
async def exportar_painel_excel(user: str = Depends(verificar_autenticacao)):
    """Download do relatório Excel do Painel Agregado (20 rotas)."""
    payload = await painel_service.obter_painel_agregado(_config)
    resultados = payload.get("resultados", [])
    xlsx_bytes = gerar_excel_visao_geral(resultados)
    
    data_str = datetime.now(_BRT).strftime("%Y%m%d_%H%M")
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="painel_rotas_{data_str}.xlsx"'},
    )


@app.get("/painel/exportar/csv")
async def exportar_painel_csv(user: str = Depends(verificar_autenticacao)):
    """Download do relatório CSV do Painel Agregado (20 rotas)."""
    payload = await painel_service.obter_painel_agregado(_config)
    resultados = payload.get("resultados", [])
    csv_str = gerar_csv_visao_geral(resultados)
    
    data_str = datetime.now(_BRT).strftime("%Y%m%d_%H%M")
    return Response(
        content=csv_str.encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="painel_rotas_{data_str}.csv"'},
    )

# --- Endpoint de consulta livre (mantido compativel) ---

@app.get("/consultar/exportar/excel")
async def exportar_consultar_excel(
    origem: str = Query(...),
    destino: str = Query(...),
    rodovia_logica: list[str] = Query(default=[]),
):
    """Alias para /exportar/excel (mantido por retrocompatibilidade)."""
    return await exportar_excel(origem=origem, destino=destino, rodovia_logica=rodovia_logica)


@app.get("/consultar/exportar/csv")
async def exportar_consultar_csv(
    origem: str = Query(...),
    destino: str = Query(...),
    rodovia_logica: list[str] = Query(default=[]),
):
    """Alias para /exportar/csv (mantido por retrocompatibilidade)."""
    return await exportar_csv(origem=origem, destino=destino, rodovia_logica=rodovia_logica)


def iniciar(config: dict, host: str = "0.0.0.0", port: int = 8000) -> None:
    """Inicia o servidor FastAPI com uvicorn."""
    global _config
    _config = config

    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info", access_log=False)
