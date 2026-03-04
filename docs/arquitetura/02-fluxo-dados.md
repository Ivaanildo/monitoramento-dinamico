# Fluxo de Dados

## Fluxo do coletor (GitHub Actions)

O coletor roda a cada 30 minutos e alimenta o Supabase com dados agregados.

```mermaid
sequenceDiagram
    participant GH as GitHub Actions
    participant C as coletor.py
    participant Consultor as consultor
    participant Google as Google Routes
    participant HERE as HERE Traffic
    participant Cache as cache
    participant Painel as painel_service
    participant Repo as repository
    participant DB as Supabase

    GH->>C: Trigger (cron 0,30 * * * *)
    C->>Consultor: consultar() para R01-R20
    par Paralelo
        Consultor->>Google: Routes API
        Consultor->>HERE: Traffic API
    end
    Google-->>Consultor: dados rota
    HERE-->>Consultor: incidentes
    Consultor->>Cache: verifica TTL
    Consultor-->>C: ResultadoRota[]
    C->>Painel: converter_para_resumo_painel()
    Painel-->>C: resumo agregado
    C->>Repo: salvar_snapshot_agregado()
    Repo->>DB: INSERT ciclos, snapshots_rotas
```

## Fluxo do painel (usuário autenticado)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant SPA as Frontend
    participant API as FastAPI
    participant Auth as auth_local
    participant Painel as painel_service
    participant DB as Supabase

    U->>SPA: Acessa /painel
    SPA->>API: GET /auth/session
    API->>Auth: verifica cookie
    Auth-->>API: sessão válida
    API-->>SPA: 200 OK
    SPA->>API: GET /painel
    API->>Painel: obter_painel_agregado()
    Painel->>DB: último ciclo + snapshots
    DB-->>Painel: dados
    Painel-->>API: painel JSON
    API-->>SPA: painel
    SPA-->>U: Renderiza PainelPage
```

## Fluxo da consulta on-demand (rota específica)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant SPA as Frontend
    participant API as FastAPI
    participant Consultor as consultor
    participant Google as Google Routes
    participant HERE as HERE Traffic

    U->>SPA: Seleciona rota em ConsultaPage
    SPA->>API: GET /rotas/{id}/consultar
    API->>Consultor: consultar(rota_id)
    Consultor->>Consultor: cache hit?
    alt Cache miss
        Consultor->>Google: Routes API
        Consultor->>HERE: Traffic API
        Google-->>Consultor: polyline, duração
        HERE-->>Consultor: incidentes
        Consultor->>Consultor: armazena em cache
    end
    Consultor-->>API: ResultadoRota
    API-->>SPA: JSON
    SPA->>SPA: MapView exibe rota + incidentes
    SPA-->>U: Mapa Leaflet
```

## Fluxo de autenticação

```mermaid
flowchart LR
    subgraph Login
        L1[POST /auth/login] --> L2[auth_local.validar]
        L2 --> L3[Cookie projeto_zero_session]
    end

    subgraph Requisições
        R1[GET /painel] --> R2[Depends require_session]
        R2 --> R3[Cookie válido?]
        R3 -->|Sim| R4[200 + dados]
        R3 -->|Não| R5[401 Unauthorized]
    end
```
