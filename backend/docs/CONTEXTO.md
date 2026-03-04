# Projeto Zero — Contexto Técnico

> Sistema on-demand de consulta de tráfego para rotas logísticas brasileiras.
> Versão atual: **1.1** | Última atualização: 2026-02-25

---

## Índice

1. [Propósito](#propósito)
2. [O que está funcionando](#o-que-está-funcionando)
3. [Arquitetura e fluxo de dados](#arquitetura-e-fluxo-de-dados)
4. [Fontes de dados](#fontes-de-dados)
5. [Estrutura de arquivos](#estrutura-de-arquivos)
6. [API endpoints](#api-endpoints)
7. [Resposta JSON (ResultadoRota)](#resposta-json-resultadorota)
8. [Classificação de status](#classificação-de-status)
9. [Estratégia de busca HERE (corridor vs bbox)](#estratégia-de-busca-here-corridor-vs-bbox)
10. [Mapa interativo](#mapa-interativo)
11. [Cache](#cache)
12. [Exportação (Excel e CSV)](#exportação-excel-e-csv)
13. [Configuração](#configuração)
14. [Observabilidade — Logs](#observabilidade--logs)
15. [Limitações conhecidas](#limitações-conhecidas)
16. [Como rodar](#como-rodar)

---

## Propósito

O **Projeto Zero** substitui a abordagem de monitoramento agendado de 28 rotas fixas por um modelo **on-demand**: o usuário informa qualquer par origem/destino e recebe em segundos o status de tráfego atual, incidentes na rota e atraso estimado.

**Premissa central:** ruído zero — só incidentes na rodovia real importam para decisão logística.

---

## O que está funcionando

### Consulta de rota
- [x] Entrada por **texto de endereço** (ex: `Campinas, SP`) ou **coordenadas** (`-23.55,-46.63`)
- [x] **Geocodificação** via HERE Geocoding API (com cache em memória)
- [x] Consulta **paralela** Google Routes API v2 + HERE Traffic (ThreadPoolExecutor 2 workers)
- [x] **Merge de status** pelo mais severo entre as duas fontes
- [x] **Cache TTL 5 min** — segunda consulta à mesma rota retorna instantaneamente

### Fontes de dados
- [x] **Google Routes API v2** — duração com tráfego, duração normal, atraso em minutos, distância, `speedReadingIntervals`
- [x] **HERE Routing v8** — polyline real da rota para corridor preciso
- [x] **HERE Traffic Incidents v7** — incidentes filtrados por corridor (raio 200m)
- [x] **HERE Flow v7** — jam factor, velocidade atual vs livre, 280+ segmentos individuais

### Mapa interativo
- [x] **Leaflet.js** com tiles OpenStreetMap (sem API key)
- [x] **Click no mapa** para definir origem (verde) e destino (vermelho)
- [x] **Polyline da rota** colorida pelo status geral
- [x] **280 flow dots** sobrepostos: cada ponto com cor do jam_factor daquele segmento
- [x] **Toast markers** de incidentes: badge flutuante com emoji + label colorida na rota
- [x] **Popup rico** ao clicar em cada toast: categoria, severidade, rodovia, descrição
- [x] **Tooltip hover** na rota: status + velocidade + atraso + Google vs HERE
- [x] **Legenda** sempre visível (escala de tráfego + ícones de incidentes)
- [x] **Badge** mostrando método de busca (`Corridor preciso` ou `BBox fallback`)

### Interface web
- [x] **Layout split**: painel esquerdo (form + resultado) + mapa direito (full height)
- [x] **Status Google vs HERE** side-by-side no painel
- [x] **6 métricas** no grid: atraso, tempo c/ trânsito, tempo normal, vel. atual, jam max, % congestionado
- [x] **Barra de confiança** com cor por nível (alta/média/baixa)
- [x] **Favoritos** persistidos em `favoritos.json` (salvar/carregar/dropdown)
- [x] **Links diretos** para Waze e Google Maps
- [x] **Download Excel** (.xlsx com estilos) e **CSV** diretamente da interface

### Exportação
- [x] Excel com cabeçalho colorido + estilo por status/confiança/ocorrência + aba separada de incidentes HERE
- [x] CSV com BOM (compatível com Excel pt-BR) incluindo todos os campos + seção de incidentes

---

## Arquitetura e fluxo de dados

```
Usuário: texto de endereço | lat,lng | clique no mapa
    │
    ▼
[cache.py] TTLCache → hit? → retorna imediatamente
    │ miss
    ▼
[consultor.py] ThreadPoolExecutor(2)
    ├── [google_traffic.py] → Google Routes API v2 (POST)
    │     └── retorna: status, atraso_min, duracao_normal/transito, distancia, razao
    └── [here_incidents.py]
          ├── Geocoding (HERE Geocoding API) → lat/lng O e D
          ├── Routing v8 (GET)  → polyline da rota bruta
          ├── [polyline.py] RDP simplify → ≤300 pts
          ├── [polyline.py] encode_corridor() → "corridor:poly;r=200"
          ├── HERE Incidents v7 (GET, corridor r=200m) → incidentes
          └── HERE Flow v7     (GET, corridor r=150m) → jam + flow_pts
    │
    ▼
[status.py]
    ├── mais_severo(google_status, here_status) → status_final
    ├── calcular_confianca(google_ok, here_ok, atraso)
    └── incidente_principal(incidentes) → categoria mais grave
    │
    ▼
ResultadoRota (dict) → salvo no cache → JSON response
    │
    └── [web/app.py] FastAPI
          ├── GET /consultar → JSONResponse
          ├── GET /exportar/excel → bytes .xlsx
          ├── GET /exportar/csv   → string .csv
          └── GET / → index.html com Leaflet + toasts
```

---

## Fontes de dados

### Google Routes API v2

| Campo | Valor |
|-------|-------|
| Endpoint | `POST https://routes.googleapis.com/directions/v2:computeRoutes` |
| Auth | Header `X-Goog-Api-Key` |
| Mode | `DRIVE` + `TRAFFIC_AWARE_OPTIMAL` |
| Retorno | `duration` (com tráfego), `staticDuration` (sem tráfego), `distanceMeters`, `speedReadingIntervals` |
| Timeout | 30s |
| Retry | 3x, backoff 0.5s, status 429/500/502/503/504 |
| Config | `config.yaml → google.api_key` ou env `GOOGLE_MAPS_API_KEY` |

### HERE Geocoding API

| Campo | Valor |
|-------|-------|
| Endpoint | `GET https://geocode.search.hereapi.com/v1/geocode` |
| Filtro | `countryCode:BRA`, `lang: pt-BR` |
| Cache | In-memory global (sem TTL — geocoord não muda) |
| Fallback | Aceita `"lat,lng"` diretamente sem geocodificar |

### HERE Routing v8

| Campo | Valor |
|-------|-------|
| Endpoint | `GET https://router.hereapi.com/v8/routes` |
| Modo | `transportMode: truck` |
| Retorno | `sections[].polyline` (flexpolyline encoded) |
| Cache | In-memory por par de coordenadas arredondadas a 4 decimais |
| Timeout | 20s |
| Uso | Gera polyline real da rota → RDP ≤300 pts → corridor string |

### HERE Traffic Incidents v7

| Campo | Valor |
|-------|-------|
| Endpoint | `GET https://data.traffic.hereapi.com/v7/incidents` |
| `in` param | `corridor:{flexpolyline};r=200` (modo corridor) |
| Fallback | `bbox:{w},{s},{e},{n}` com padding 5km |
| `locationReferencing` | `shape` (retorna geometria dos incidentes) |
| Timeout | 12s por requisição |
| Resultado típico | Campinas→SP: **2 relevantes** (vs 255 com bbox antigo) |

### HERE Traffic Flow v7

| Campo | Valor |
|-------|-------|
| Endpoint | `GET https://data.traffic.hereapi.com/v7/flow` |
| `in` param | `corridor:{flexpolyline};r=150` (raio menor que incidents) |
| Retorno | `currentFlow.speed` (m/s), `currentFlow.freeFlow` (m/s), `currentFlow.jamFactor` (0-10) |
| `flow_pts` | Até 400 centroides de segmentos com `{lat, lng, jam}` para heatmap no mapa |
| Conversão | `speed * 3.6` → km/h |

---

## Estrutura de arquivos

```
projeto_zero/
│
├── CONTEXTO.md               ← este arquivo
├── config.yaml               ← API keys + TTL cache + host/porta
├── favoritos.json            ← rotas salvas pelo usuário
├── requirements.txt          ← 6 dependências
├── main.py                   ← CLI: --web | --consultar "A" "B" [--json]
│
├── core/
│   ├── consultor.py          ← orquestrador on-demand; monta ResultadoRota
│   ├── google_traffic.py     ← Google Routes API v2 (single-route)
│   ├── here_incidents.py     ← HERE Geocoding + Routing v8 + Incidents + Flow
│   ├── polyline.py           ← RDP, haversine, encode_corridor, decode_polyline, geojson
│   ├── status.py             ← thresholds, classificar_transito, mais_severo, confiança
│   └── cache.py              ← TTLCache thread-safe (singleton global)
│
├── report/
│   └── excel_simple.py       ← gerar_excel() → bytes .xlsx | gerar_csv() → str
│
└── web/
    ├── app.py                ← FastAPI 8 endpoints
    └── static/
        └── index.html        ← SPA Leaflet.js (layout split, toasts, flow heatmap)
```

### Descrição dos módulos principais

**`core/consultor.py`** — ponto de entrada de toda consulta. Verifica cache, dispara Google + HERE em paralelo, faz merge de status, calcula confiança, monta o `ResultadoRota` completo e salva no cache.

**`core/here_incidents.py`** — módulo mais complexo. Geocodifica O/D, obtém polyline via Routing v8, simplifica com RDP, codifica corridor, consulta Incidents e Flow, extrai `flow_pts` para heatmap. Fallback automático para bbox se qualquer etapa do corridor falhar.

**`core/polyline.py`** — utilitários geométricos: RDP iterativo (preserva curvas), `downsample_polyline` (≤300 pts garantido), `encode_corridor` (flexpolyline → string HERE), `decode_polyline` (flexpolyline → lista de tuplas), `pts_to_geojson_line` (para Leaflet).

**`core/status.py`** — lógica de classificação portada do monitor-rodovias: combina razão de duração + atraso absoluto (corrige rotas longas onde 25min de atraso tem razão baixa). Jam factor máximo prevalece sobre média (captura congestionamentos localizados).

**`web/app.py`** — FastAPI com 8 rotas. Sem banco de dados, sem autenticação. Config injetada via global `_config` após `iniciar()`.

---

## API endpoints

| Método | Rota | Parâmetros | Retorno |
|--------|------|-----------|---------|
| `GET` | `/` | — | `index.html` (SPA) |
| `GET` | `/consultar` | `origem`, `destino` | JSON `ResultadoRota` |
| `GET` | `/exportar/excel` | `origem`, `destino` | `.xlsx` (download) |
| `GET` | `/exportar/csv` | `origem`, `destino` | `.csv` (download, BOM UTF-8) |
| `GET` | `/favoritos` | — | `{"favoritos": [...]}` |
| `POST` | `/favoritos` | body `{nome, origem, destino}` | `{"message": "...", "favoritos": [...]}` |
| `DELETE` | `/favoritos` | `origem`, `destino` | lista atualizada |
| `GET` | `/cache/info` | — | `{"tamanho": N, "ttl_segundos": 300}` |
| `DELETE` | `/cache` | — | `{"message": "Cache limpo"}` |

**Validações automáticas:** origem/destino obrigatórios, não podem ser iguais. HTTP 400 com `detail` descritivo.

---

## Resposta JSON (ResultadoRota)

```jsonc
{
  // Identificação
  "origem":  "Campinas, SP",
  "destino": "São Paulo, SP",

  // Status consolidado
  "status":        "Intenso",      // Normal | Moderado | Intenso | Parado | Sem dados
  "status_google": "Moderado",     // status calculado pela fonte Google
  "status_here":   "Intenso",      // status calculado pela fonte HERE

  // Métricas de tempo (Google)
  "atraso_min":            15,
  "duracao_normal_min":    88,
  "duracao_transito_min":  103,
  "distancia_km":          101.1,
  "razao_transito":        1.17,

  // Métricas HERE Flow
  "jam_factor_avg":        3.3,
  "jam_factor_max":        9.3,
  "velocidade_atual_kmh":  32.5,
  "velocidade_livre_kmh":  44.9,
  "pct_congestionado":     38.2,  // % de segmentos com jam >= 5

  // Incidentes HERE
  "incidentes": [
    {
      "categoria":       "Colisão",      // Colisão | Bloqueio Parcial | Interdição | Obras na Pista | Engarrafamento | ...
      "severidade":      "Alta",         // Baixa | Média | Alta | Crítica
      "severidade_id":   3,
      "descricao":       "[BR-116] Acidente | Colisão ...",
      "rodovia_afetada": "BR-116",
      "road_closed":     false,
      "road_closed_raw": false,
      "bloqueio_escopo": "nenhum",       // total | parcial | nenhum
      "causa_detectada": "acidente",     // acidente | obra | risco | clima | indefinida
      "tipo_raw":        "accident",
      "latitude":        -23.1234,
      "longitude":       -46.5678,
      "inicio":          "2026-02-25T14:00:00Z",
      "fim":             "",
      "fonte":           "HERE Traffic"
    }
  ],
  "incidente_principal": "Colisão",    // categoria do mais grave

  // Confiança
  "confianca":     "Alta",             // Alta | Média | Baixa
  "confianca_pct": 90,

  // Geometria da rota (para Leaflet)
  "route_pts":    [[-23.55, -46.63], ...],   // lista de [lat, lng] — da Routing v8
  "route_geojson": { "type": "Feature", "geometry": {"type": "LineString", ...} },

  // Heatmap de fluxo (para flow dots no mapa)
  "flow_pts": [
    {"lat": -23.551, "lng": -46.641, "jam": 7.2},
    ...
  ],  // até 400 pontos, centroide de cada segmento HERE Flow

  // Metadados
  "metodo_busca":   "corridor",        // corridor | bbox
  "fontes":         ["Google Routes API v2", "HERE Traffic"],
  "link_waze":      "https://waze.com/ul?...",
  "link_gmaps":     "https://www.google.com/maps/dir/...",
  "consultado_em":  "2026-02-25 16:48:06",  // UTC
  "cache_hit":      false,
  "erros": {
    "google": "",   // string vazia = sem erro
    "here":   ""
  }
}
```

---

## Classificação de status

### Google (baseado em duração)

| Status | Razão (transito/normal) | Atraso absoluto |
|--------|------------------------|-----------------|
| Normal | ≤ 1.15 | < 10 min |
| Moderado | > 1.15 | ≥ 10 min (razão > 1.03) |
| Intenso | > 1.40 | ≥ 25 min (razão > 1.05) |

> O atraso absoluto corrige o problema de rotas longas: uma viagem de 1000km com 25min de atraso tem razão ~1.04 (seria "Normal"), mas o atraso real de 25min é logisticamente relevante → "Intenso".

### HERE (baseado em jam factor)

| Status | Condição |
|--------|----------|
| Normal | jam_max < 5 e jam_avg < 5 |
| Moderado | jam_max ≥ 5 ou jam_avg ≥ 5 |
| Intenso | jam_max ≥ 8 |
| Parado | jam_max ≥ 10 ou `road_closed = true` |

> Usa `jam_factor_max` (não média) para capturar congestionamentos localizados. Sem isso, 50km parados + 380km livres dariam média baixa e status "Normal".

### Merge final

```
status_final = mais_severo(status_google, status_here)
```

O mais severo entre as duas fontes sempre vence.

### Confiança

| Situação | Label | % base |
|----------|-------|--------|
| Ambas ok | Alta | 90% |
| Apenas uma | Média | 60% |
| Nenhuma | Baixa | 20% |

Penalidade de -10% se atraso ≥ 90 min (dados possivelmente fora do comum).

---

## Estratégia de busca HERE (corridor vs bbox)

### Corridor preciso (padrão)

```
1. HERE Routing v8 → polyline bruta (ex: 1296 pts)
2. RDP simplify → ≤300 pts (ex: 92 pts)
3. flexpolyline encode → string compacta
4. Incidents: corridor:poly;r=200   (200m de raio)
5. Flow:      corridor:poly;r=150   (150m de raio)
```

O corridor reduz ruído geométrico, mas não é validação semântica suficiente:
- incidentes continuam passando por filtro textual de rodovia quando a rota possui `rodovia_logica` reconhecível
- incidentes sem BR explícita são descartados mesmo se estiverem geometricamente dentro do corredor

**Resultado prático:** Campinas → São Paulo
- Bbox antigo: **255 incidentes** (toda a área urbana da rota)
- Corridor atual: **2 incidentes** (apenas na rodovia real)
- Redução de ruído: **99.2%**

### Fallback bbox (automático se Routing v8 falhar)

```
padding = 5km por lado
n_boxes = até 6 distribuídos ao longo da rota
+ filtro por código de rodovia (BR/SP/PR/...) para rotas > 500km
```

### Coloração dos flow dots no mapa

| Jam Factor | Cor | Significado visual |
|-----------|-----|-------------------|
| < 1 | Azul (`#3498db`) | Sem dado de congestion |
| 1–3 | Verde (`#27ae60`) | Tráfego normal |
| 3–6 | Amarelo (`#f39c12`) | Moderado |
| 6–8 | Laranja (`#e67e22`) | Intenso |
| ≥ 8 | Vermelho (`#c0392b`) | Parado / congestionado |

---

## Mapa interativo

### Camadas desenhadas (em ordem)

1. **Polyline base da rota** — colorida pelo `status` geral (verde/amarelo/laranja/vermelho), opacidade 85%, glow de fundo
2. **Flow dots (canvas renderer)** — 280+ círculos sobrepostos na rota, cada um com a cor do `jam_factor` daquele segmento específico — cria efeito de heatmap
3. **Toast markers de incidentes** — `L.divIcon` com badge flutuante (borda esquerda colorida + emoji + label), listrado quando `road_closed`
4. **Marcadores de O/D** — círculos verde (origem) e vermelho (destino), posicionados nos extremos do `route_pts`

### Interações

- **Click no mapa** → define origem (1º clique) ou destino (2º clique); alterna automaticamente
- **Botões "Definir Origem/Destino"** → seleciona modo manualmente
- **Hover na rota** → tooltip com status + velocidade + atraso + Google vs HERE
- **Click em toast** → popup com detalhes completos do incidente
- **Botão Limpar** → remove todos os marcadores e limpa os campos

### Categorias de incidentes (ícones)

| Categoria | Emoji | Cor borda |
|-----------|-------|-----------|
| Interdição | 🚧 | `#922b21` (vermelho escuro) |
| Colisão | 💥 | `#e74c3c` (vermelho) |
| Obras na Pista | 🔧 | `#e67e22` (laranja) |
| Engarrafamento | 🐌 | `#e6b800` (amarelo) |
| Condição Climática | ⛈ | `#2980b9` (azul) |
| Ocorrência | ⚠️ | `#7f8c8d` (cinza) |
| Road Closed (qualquer) | — | fundo listrado + `#922b21` |

---

## Cache

**Implementação:** `TTLCache` — dict em memória + `threading.Lock()` + `time.monotonic()`

```
Chave = "origem_normalizada|destino_normalizada"  (lowercase, strip)
TTL   = 300 segundos (5 min) — configurável via config.yaml
```

**Comportamento:**
- Cache hit → retorna imediatamente + seta `cache_hit: true` no JSON
- Cache miss → consulta APIs em paralelo, salva resultado
- `DELETE /cache` → limpa tudo, força nova consulta às APIs
- `GET /cache/info` → retorna tamanho atual e TTL configurado

**Thread-safety:** lock por operação. Singleton global criado na primeira chamada a `get_cache()`.

---

## Exportação (Excel e CSV)

### Excel (.xlsx)

**Aba "Consulta"** (11 colunas):

| Col | Campo | Estilo |
|-----|-------|--------|
| A | Rota (Origem → Destino) | Alinhamento esquerda |
| B | Status | Fundo colorido por valor |
| C | Atraso (min) | — |
| D | Confiança | Fundo colorido (verde/amarelo/vermelho) |
| E | Incidente Principal | Fundo colorido por categoria |
| F | Vel. Atual (km/h) | — |
| G | Jam Factor | — |
| H | Fontes | — |
| I | Atualizado em | — |
| J | Link Waze | Hyperlink azul sublinhado |
| K | Link Google Maps | Hyperlink azul sublinhado |

**Aba "Incidentes HERE"** (gerada se houver incidentes, 8 colunas):
`#` | Categoria | Severidade | Rodovia | Road Closed | Descrição | Início | Fim

### CSV

Mesmas colunas da aba principal + campos extras (`jam_factor_max`, `distancia_km`, `razao_transito`) + seção `=== Incidentes HERE ===` abaixo.

Encoding: **UTF-8 com BOM** (`utf-8-sig`) para compatibilidade com Excel em pt-BR.

---

## Configuração

**`config.yaml`:**

```yaml
google:
  api_key: ""          # opcional — ou env GOOGLE_MAPS_API_KEY

here:
  api_key: ""          # obrigatório para map + incidents + flow
                       # ou env HERE_API_KEY

cache:
  ttl_segundos: 300    # TTL do cache em memória (padrão: 5 min)

web:
  host: "0.0.0.0"     # interface de escuta
  port: 8000           # porta HTTP
```

**Ordem de resolução das API keys:**
1. Campo `api_key` no `config.yaml`
2. Variável de ambiente (`GOOGLE_MAPS_API_KEY` / `HERE_API_KEY`)
3. String vazia → fonte desabilitada (retorna erro no campo `erros`)

**Sem Google key:** sistema funciona apenas com HERE. Status baseado em jam factor.
**Sem HERE key:** sistema funciona apenas com Google. Sem incidentes, sem heatmap, sem polyline da rota.

---

## Observabilidade — Logs

Formato padrão: `HH:MM:SS [LEVEL] módulo: mensagem`

### Logs por etapa de uma consulta

```
16:48:00 [INFO] core.google_traffic: Google Routes: Moderado | 103min (normal: 88min, atraso: 15min, distância: 101.1km)
16:48:04 [INFO] core.here_incidents: HERE Routing v8: 1296 pts brutos → 92 pts simplificados
16:48:04 [INFO] core.here_incidents: HERE: rota 84km | corridor (92 pts) | raio incidents=200m flow=150m
16:48:05 [INFO] core.here_incidents: HERE Incidents: 2 brutos -> 2 relevantes
16:48:06 [INFO] core.here_incidents: HERE Flow: Intenso | jam_avg=3.3 jam_max=9.3 vel=32.5km/h (livre=44.9km/h)
16:48:06 [INFO] core.consultor: Consulta: Campinas, SP → São Paulo, SP | Status=Intenso | Atraso=15min | Confiança=Alta(90%)
```

### Log de cache hit

```
16:48:13 [INFO] core.consultor: Cache hit: Campinas, SP → São Paulo, SP
```

### Log de fallback bbox

```
[INFO] core.here_incidents: HERE: rota 84km | bbox fallback (4 bbox(es)) | filtro rodovias=sim
[INFO] core.here_incidents: Filtro bbox (84km): 12 descartados, 2 mantidos
```

### O que monitorar em produção

| Sinal | O que indica |
|-------|-------------|
| `HERE Routing v8: N pts brutos → M pts` | corridor ativo; M ≤ 300 = OK |
| `metodo_busca: bbox` | Routing v8 falhou; resultado menos preciso |
| `0 brutos -> 0 relevantes` | rota sem incidentes (normal) |
| `Geocoding falhou para '...'` | endereço não reconhecido pela HERE Geocoding |
| `HTTP_4xx / HTTP_5xx` na fonte | API key inválida ou rate limit |
| `jam_max >= 9` + `Parado` | congestionamento crítico |
| Tempo de resposta > 15s | possível timeout de API; verificar conexão |

---

## Limitações conhecidas

### Técnicas

| Limitação | Detalhe |
|-----------|---------|
| **Google key obrigatória para atraso** | Sem Google key, `atraso_min` será sempre 0; status baseado apenas em jam factor |
| **Coordenadas na entrada** | Ao clicar no mapa, o campo mostra `lat,lng`. O backend resolve corretamente, mas não exibe nome do endereço |
| **HERE corridor: max 1400 chars** | Para rotas muito longas (> ~2000km), o corridor pode ser truncado; o módulo reduz automaticamente para 150 pts nesse caso |
| **Cache global sem partição** | Múltiplos usuários compartilham o mesmo cache (adequado para uso logístico interno, não multi-tenant) |
| **Sem autenticação** | API e interface abertas; adequado para rede interna |
| **Flow dots: sem geometria de linha** | `flow_pts` são centroides de segmentos, não polylines; a visualização é de pontos, não de trechos coloridos |

### De dados

| Limitação | Detalhe |
|-----------|---------|
| **HERE gratuito: rate limit** | ~250 req/mês no plano free; para uso intenso, considerar plano pago |
| **Google Routes gratuito** | $200 crédito/mês; ~4000 consultas de rota gratuitas |
| **Incidentes sem coordenadas** | Alguns incidentes HERE não retornam geometria; não aparecem no mapa (aparecem na lista do painel) |
| **Rotas fora do Brasil** | Geocodificação forçada para `countryCode:BRA`; endereços em outros países falharão |

---

## Como rodar

### Instalação

```bash
cd projeto_zero
python -m pip install -r requirements.txt
```

### Configurar API keys

Edite `config.yaml`:
```yaml
here:
  api_key: "SUA_CHAVE_HERE"
google:
  api_key: "SUA_CHAVE_GOOGLE"
```

Ou via variáveis de ambiente:
```bash
export HERE_API_KEY="SUA_CHAVE_HERE"
export GOOGLE_MAPS_API_KEY="SUA_CHAVE_GOOGLE"
```

### Iniciar servidor web

```bash
python main.py --web
# Acesse: http://localhost:8000
```

### Consulta via CLI

```bash
python main.py --consultar "Campinas, SP" "São Paulo, SP"
python main.py --consultar "Campinas, SP" "São Paulo, SP" --json
```

### Consulta via API

```bash
curl "http://localhost:8000/consultar?origem=Campinas,SP&destino=S%C3%A3o+Paulo,SP"
```

### Gerenciar cache

```bash
# Ver status
curl http://localhost:8000/cache/info

# Limpar (força nova consulta às APIs)
curl -X DELETE http://localhost:8000/cache
```

---

## Dependências

```
fastapi>=0.110.0,<1.0.0     # framework web
uvicorn>=0.29.0,<1.0.0      # servidor ASGI
requests>=2.31.0,<3.0.0     # chamadas HTTP às APIs
openpyxl>=3.1.0,<4.0.0      # geração de Excel
pyyaml>=6.0.1,<7.0.0        # leitura do config.yaml
flexpolyline>=1.0.1,<2.0.0  # encode/decode polyline HERE (corridor)
```

Sem banco de dados, sem ORM, sem message broker, sem autenticação, sem dependências nativas. Roda em qualquer Python 3.10+.
