# Fluxo de Dados

## Coleta periodica

O workflow do GitHub Actions roda **a cada hora** e executa o worker diretamente. O backend web nao participa desse ciclo.

```mermaid
sequenceDiagram
    participant GH as GitHub Actions
    participant W as workers/coletor.py
    participant C as consultor
    participant G as Google Routes
    participant H as HERE Traffic
    participant P as painel_service
    participant R as repository
    participant DB as Supabase

    GH->>W: cron 0 * * * *
    W->>C: consultar 20 rotas
    par Fontes externas
        C->>G: tempo de rota
        C->>H: incidentes e fluxo
    end
    G-->>C: duracao e atraso
    H-->>C: incidentes e jam factor
    C-->>W: resultado detalhado
    W->>P: converter para resumo do painel
    W->>R: salvar_snapshot_agregado()
    R->>DB: ciclos + snapshots_rotas
```

## Painel agregado

```mermaid
sequenceDiagram
    participant U as Usuario
    participant SPA as Frontend
    participant API as FastAPI
    participant Auth as auth_local
    participant Painel as painel_service
    participant DB as Supabase

    U->>SPA: abre /painel
    SPA->>API: GET /api/auth/session
    API->>Auth: validar cookie
    Auth-->>API: sessao valida
    SPA->>API: GET /api/painel
    API->>Painel: obter_painel_agregado()
    Painel->>DB: ultimo ciclo + snapshots
    DB-->>Painel: linhas do painel
    Painel-->>API: payload agregado
    API-->>SPA: JSON
```

## Consulta detalhada

```mermaid
sequenceDiagram
    participant U as Usuario
    participant SPA as Frontend
    participant API as FastAPI
    participant C as consultor
    participant G as Google Routes
    participant H as HERE Traffic

    U->>SPA: abre /consulta?rota_id=Rxx
    SPA->>API: GET /api/rotas/{id}/snapshot
    API-->>SPA: snapshot rapido
    SPA->>API: GET /api/rotas/{id}/consultar
    API->>C: consultar rota corporativa
    par Fontes externas
        C->>G: Routes API
        C->>H: Traffic API
    end
    C-->>API: resultado detalhado
    API-->>SPA: JSON com polyline, incidentes e metricas
```

## Autenticacao local

```mermaid
flowchart LR
    Login["POST /auth/login"] --> Cookie["Cookie de sessao"]
    Cookie --> Protegidas["/rotas, /painel, /favoritos, /cache"]
    Protegidas --> Valida["Depends(verificar_autenticacao)"]
```
