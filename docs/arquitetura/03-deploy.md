# Arquitetura de Deploy

## Topologia atual

```mermaid
flowchart TB
    User["Usuario"] --> Vercel["Vercel"]
    Vercel --> SPA["frontend/dist"]
    Vercel -->|/api/:path*| PublicAPI["Backend publico"]
    PublicAPI --> Google["Google Routes API"]
    PublicAPI --> Here["HERE Traffic API"]
    PublicAPI --> Supabase["Supabase"]
    GHA["GitHub Actions"] --> Worker["backend/workers/coletor.py"]
    Worker --> Google
    Worker --> Here
    Worker --> Supabase
```

## Rewrites do frontend

O contrato em producao esta centralizado em [`../../vercel.json`](../../vercel.json).

Regras relevantes:

| Source | Destino |
| --- | --- |
| `/api/:path*` | backend publico configurado no `vercel.json` |
| `/(.*)` | `/index.html` |

Observacao importante:

- o frontend sempre chama `"/api/*"`;
- a remocao do prefixo `/api` e responsabilidade da camada de rewrite/proxy.

## Build do frontend

```mermaid
flowchart LR
    Install["cd frontend && npm ci"] --> Build["npm run build"]
    Build --> Dist["frontend/dist"]
    Dist --> Vercel["Vercel output"]
```

## Workflow do worker

```mermaid
flowchart LR
    Trigger["schedule + workflow_dispatch"] --> Checkout["actions/checkout"]
    Checkout --> Python["actions/setup-python 3.11"]
    Python --> Deps["pip install -r backend/requirements.txt"]
    Deps --> Run["python workers/coletor.py"]
    Run --> Artifact["upload-artifact backend/relatorios"]
```

## Segredos operacionais

| Variavel | Uso |
| --- | --- |
| `GOOGLE_MAPS_API_KEY` | consulta Google Routes |
| `HERE_API_KEY` | consulta HERE |
| `SUPABASE_URL` | endpoint do banco |
| `SUPABASE_SERVICE_ROLE_KEY` | escrita de snapshots |
| `SUPABASE_KEY` | compatibilidade legada |
