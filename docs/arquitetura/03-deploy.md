# Arquitetura de Deploy

## Infraestrutura em produção

```mermaid
flowchart TB
    subgraph CDN["🌐 CDN / Edge"]
        Vercel[Vercel Edge]
    end

    subgraph Frontend["Frontend"]
        SPA[SPA estático<br/>frontend/dist]
    end

    subgraph Backend["Backend"]
        Render[Render.com<br/>monitoramento-dinamico-api]
    end

    subgraph CI["CI/CD"]
        GHA[GitHub Actions<br/>monitor_dinamico.yml]
    end

    subgraph External["Externos"]
        Google[Google API]
        HERE[HERE API]
        Supabase[Supabase]
    end

    User[Usuário] --> Vercel
    Vercel --> SPA
    Vercel -->|rewrites| Render
    SPA -->|/auth, /painel, /rotas| Render
    Render --> Google
    Render --> HERE
    Render --> Supabase
    GHA -.->|coletor.py| Render
    GHA -.->|secrets| Google
    GHA -.->|secrets| HERE
    GHA -.->|secrets| Supabase
```

## Rewrites do Vercel

```mermaid
flowchart LR
    subgraph Vercel
        R1["/auth/:path*"] --> API
        R2["/painel"] --> API
        R3["/painel/:path*"] --> API
        R4["/rotas/:path*"] --> API
        R5["/(.*)"] --> Index[index.html]
    end

    API[API Render]
```

| Source | Destination |
|--------|-------------|
| `/auth/:path*` | `https://monitoramento-dinamico-api.onrender.com/auth/:path*` |
| `/painel`, `/painel/:path*` | API Render |
| `/rotas/:path*` | API Render |
| `/(.*)` | `/index.html` (SPA fallback) |

## Pipeline de build

```mermaid
flowchart LR
    subgraph Build
        B1[cd frontend] --> B2[npm ci]
        B2 --> B3[npm run build]
        B3 --> B4[frontend/dist]
    end

    subgraph Deploy
        D1[Vercel] --> D2[Output: frontend/dist]
    end
```

## GitHub Actions — Coletor

```mermaid
flowchart TB
    subgraph Trigger
        Cron["cron: 0,30 * * * *"]
        Manual["workflow_dispatch"]
    end

    subgraph Job
        J1[Checkout] --> J2[Setup Python]
        J2 --> J3[Install deps]
        J3 --> J4[Run coletor.py]
    end

    subgraph Secrets
        S1[GOOGLE_MAPS_API_KEY]
        S2[HERE_API_KEY]
        S3[SUPABASE_URL]
        S4[SUPABASE_KEY]
    end

    Cron --> Job
    Manual --> Job
    J4 --> S1
    J4 --> S2
    J4 --> S3
    J4 --> S4
```
