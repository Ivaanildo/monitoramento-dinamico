# Arquitetura

Este diretorio concentra os diagramas que explicam a topologia real do projeto.

## Leituras

| Arquivo | Foco |
| --- | --- |
| [01-visao-geral.md](01-visao-geral.md) | componentes, responsabilidades e integracoes |
| [02-fluxo-dados.md](02-fluxo-dados.md) | painel, consulta detalhada e worker |
| [03-deploy.md](03-deploy.md) | entrega web, rewrite de API e automacao |
| [04-estrutura-codebase.md](04-estrutura-codebase.md) | mapa de pastas e modulos principais |

## Stack resumida

| Camada | Tecnologias |
| --- | --- |
| Frontend | React 18, Vite 6, React Router, Tailwind 4, Motion, Leaflet |
| Backend | Python 3.11, FastAPI, Uvicorn, httpx |
| Dados | Supabase |
| Externos | Google Routes API, HERE Traffic API |
| Automacao | GitHub Actions |

## Renderizacao dos diagramas

Os arquivos usam Mermaid em fenced code blocks, que o GitHub renderiza nativamente em Markdown.
