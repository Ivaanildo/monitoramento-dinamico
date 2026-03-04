# Arquitetura — Monitoramento Dinâmico

Esta pasta contém os diagramas de arquitetura do projeto **Monitoramento Dinâmico**, um sistema de monitoramento de trânsito em tempo real com rotas corporativas (R01–R20).

## Diagramas disponíveis

| Arquivo | Descrição |
|---------|-----------|
| [01-visao-geral.md](01-visao-geral.md) | Visão geral do sistema: componentes, tecnologias e integrações |
| [02-fluxo-dados.md](02-fluxo-dados.md) | Fluxo de dados: coletor, painel, consulta on-demand |
| [03-deploy.md](03-deploy.md) | Arquitetura de deploy: Vercel, Render, GitHub Actions |
| [04-estrutura-codebase.md](04-estrutura-codebase.md) | Estrutura de pastas e módulos do código |

## Stack tecnológica

| Camada | Tecnologias |
|--------|-------------|
| **Frontend** | React 18, Vite 6, React Router 7, Tailwind 4, Motion, Leaflet, Radix UI, Recharts |
| **Backend** | Python 3.11, FastAPI, Uvicorn, httpx |
| **APIs externas** | Google Routes API v2, HERE Traffic API |
| **Banco** | Supabase (REST API) |
| **Deploy** | Vercel (frontend), Render (API), GitHub Actions (coletor) |

## Como visualizar os diagramas

Os diagramas usam **Mermaid**. Para visualizar:

- **VS Code / Cursor**: extensão "Markdown Preview Mermaid Support"
- **GitHub**: renderização automática em arquivos `.md`
- **Online**: [Mermaid Live Editor](https://mermaid.live/)
