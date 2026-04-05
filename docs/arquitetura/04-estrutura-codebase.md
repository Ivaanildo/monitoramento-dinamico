# Estrutura do Codebase

## Mapa rapido

```mermaid
flowchart TB
    Root["Monitoramento_Dinamico"] --> Frontend["frontend"]
    Root --> Backend["backend"]
    Root --> Docs["docs"]
    Root --> Presentation["presentation"]
    Root --> Workflow[".github/workflows"]
```

## Frontend

| Caminho | Papel |
| --- | --- |
| `frontend/src/app/App.tsx` | roteamento principal |
| `frontend/src/app/pages/LoginPage.tsx` | login local |
| `frontend/src/app/pages/PainelPage.tsx` | grid operacional das rotas |
| `frontend/src/app/pages/ConsultaPage.tsx` | visao detalhada da rota |
| `frontend/src/app/services/api.ts` | cliente HTTP baseado em `/api` |
| `frontend/src/app/components/` | componentes visuais, mapa, cards e gauges |
| `frontend/vite.config.ts` | build, versionamento e proxy local |

## Backend

| Caminho | Papel |
| --- | --- |
| `backend/main.py` | entrada CLI e modo web |
| `backend/web/app.py` | aplicacao FastAPI e endpoints |
| `backend/core/consultor.py` | consulta e merge Google/HERE |
| `backend/core/painel_service.py` | resumo agregado do painel |
| `backend/core/auth_local.py` | autenticacao e sessao |
| `backend/core/config_loader.py` | configuracao com override por env var |
| `backend/storage/database.py` | cliente Supabase |
| `backend/storage/repository.py` | persistencia de snapshots |
| `backend/report/excel_simple.py` | exportacao Excel/CSV |
| `backend/workers/coletor.py` | worker agendado |
| `backend/tests/` | suite pytest |

## Dados e configuracao

| Caminho | Papel |
| --- | --- |
| `backend/data/rotas.json` | cadastro de 20 rotas corporativas |
| `backend/config.yaml` | defaults publicos da aplicacao |
| `backend/.env.example` | referencia de variaveis |
| `vercel.json` | build do frontend e rewrite de API |

## Rotas do frontend

```mermaid
flowchart LR
    Root["/"] --> Painel["/painel"]
    Login["/login"] --> Auth["LoginPage"]
    Painel --> Grid["PainelPage"]
    Consulta["/consulta?rota_id=Rxx"] --> Detail["ConsultaPage"]
```

## Grupos de rotas da API

```mermaid
flowchart LR
    Publico["Publico"] --> Health["/healthz"]
    Publico --> Auth["/auth/*"]
    Publico --> Consultar["/consultar e exportacoes livres"]
    Protegido["Protegido por cookie"] --> Painel["/painel*"]
    Protegido --> Rotas["/rotas*"]
    Protegido --> Favoritos["/favoritos"]
    Protegido --> Cache["/cache*"]
```
