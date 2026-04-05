# Visao Geral da Arquitetura

## Topologia principal

```mermaid
flowchart TB
    Usuario["Usuario / Operacao"] --> Vercel["Frontend hospedado"]
    Vercel --> SPA["SPA React + Vite"]
    SPA -->|/api/*| API["FastAPI"]
    API --> Google["Google Routes API"]
    API --> Here["HERE Traffic API"]
    API --> Supabase["Supabase"]
    GHA["GitHub Actions"] --> Worker["workers/coletor.py"]
    Worker --> Google
    Worker --> Here
    Worker --> Supabase
```

## Responsabilidades por bloco

| Bloco | Responsabilidade |
| --- | --- |
| Frontend | login local, painel agregado, consulta detalhada e exportacao local |
| FastAPI | auth, consulta on-demand, agregacao do painel, exportacao de relatorios |
| Worker | coleta horaria, consolidacao e persistencia de snapshots |
| Supabase | armazenamento de ciclos e snapshots |
| APIs externas | tempo de rota, incidentes, velocidade e jam factor |

## Camadas internas do backend

```mermaid
flowchart LR
    App["web/app.py"] --> Core["core/*"]
    App --> Report["report/excel_simple.py"]
    Core --> Storage["storage/*"]
    Core --> External["Google + HERE"]
    Storage --> Supabase["Supabase REST"]
```

## Componentes de negocio mais relevantes

| Arquivo | Papel |
| --- | --- |
| `backend/core/consultor.py` | merge de Google e HERE em consulta detalhada |
| `backend/core/painel_service.py` | conversao para o contrato agregado do painel |
| `backend/core/auth_local.py` | sessao por cookie e validacao local |
| `backend/storage/repository.py` | escrita de snapshots no Supabase |
| `backend/workers/coletor.py` | coleta automatica das 20 rotas |
