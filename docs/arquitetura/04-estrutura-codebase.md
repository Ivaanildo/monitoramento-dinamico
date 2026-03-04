# Estrutura do Codebase

## Árvore de diretórios

```mermaid
flowchart TB
    subgraph Root["Monitoramento_Dinamico/"]
        subgraph Frontend["frontend/"]
            F1[src/app/pages/]
            F2[src/app/components/]
            F3[src/app/services/]
            F4[vite.config.ts]
        end
        subgraph Backend["backend/"]
            B1[web/app.py]
            B2[core/]
            B3[storage/]
            B4[workers/]
            B5[report/]
        end
        subgraph Config["Config"]
            C1[vercel.json]
            C2[.github/workflows/]
        end
    end
```

## Detalhamento das pastas

### Frontend (`frontend/`)

| Pasta/Arquivo | Descrição |
|---------------|-----------|
| `src/app/pages/` | LoginPage, PainelPage, ConsultaPage |
| `src/app/components/` | MapView, RouteCard, GaugeChart, FilterDropdown, StatusTicker, RadarIcon, ui/* |
| `src/app/services/api.ts` | Cliente HTTP com `credentials: "include"` |
| `src/styles/` | index.css, tailwind.css, theme.css, fonts.css |

### Backend (`backend/`)

| Pasta/Arquivo | Descrição |
|---------------|-----------|
| `web/app.py` | Servidor FastAPI principal, rotas |
| `core/consultor.py` | Orquestrador de consultas (Google + HERE em paralelo) |
| `core/painel_service.py` | Agregação do painel (20 rotas) |
| `core/rotas_corporativas.py` | Carregamento de rotas.json |
| `core/auth_local.py` | Autenticação por cookie |
| `core/config_loader.py` | Carregamento de config.yaml |
| `core/cache.py` | Cache em memória (TTL 300s) |
| `core/google_traffic.py` | Integração Google Routes API |
| `core/here_incidents.py` | Integração HERE Traffic API |
| `storage/database.py` | Cliente Supabase (httpx) |
| `storage/repository.py` | Persistência de snapshots |
| `report/excel_simple.py` | Exportação Excel/CSV |
| `workers/coletor.py` | Job de polling (GitHub Actions) |

### Configurações

| Arquivo | Descrição |
|---------|-----------|
| `config.yaml` | API keys, cache, auth, Supabase |
| `rotas.json` | Rotas corporativas R01–R20 |
| `favoritos.json` | Favoritos + rotas predefinidas |

## Rotas da API (FastAPI)

```mermaid
flowchart TB
    subgraph Publicas["Públicas"]
        P1[GET /healthz]
        P2[POST /auth/login]
        P3[GET /consultar]
        P4[GET /favoritos]
    end

    subgraph Protegidas["Protegidas (cookie)"]
        R1[GET /rotas]
        R2[GET /rotas/:id]
        R3[GET /rotas/:id/consultar]
        R4[GET /painel]
        R5[GET /painel/exportar/excel]
        R6[GET /painel/exportar/csv]
    end
```

## Rotas do Frontend (React Router)

```mermaid
flowchart LR
    R["/"] --> Redirect["→ /painel"]
    L["/login"] --> LoginPage
    P["/painel"] --> PainelPage
    C["/consulta"] --> ConsultaPage
```
