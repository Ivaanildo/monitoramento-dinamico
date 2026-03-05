# Monitoramento Dinamico

Repositorio publico para monitoramento de rotas com frontend web em React/Vite e backend em FastAPI.

## Visao Geral

O projeto combina:

- uma interface web para consulta de rotas, painel operacional e autenticacao local;
- uma API backend para agregacao, consulta e exportacao de dados;
- um worker de coleta para atualizacao periodica de snapshots;
- uma base de dados versionada com rotas e favoritos publicos do projeto.

## Stack Tecnica

### Frontend

- React 18
- Vite 6
- TypeScript
- Tailwind CSS 4
- Radix UI
- MUI
- Recharts
- React Router
- React Hook Form
- Leaflet / React Leaflet

### Backend

- Python 3
- FastAPI
- Uvicorn
- HTTPX
- Requests
- PyYAML
- OpenPyXL

### Infraestrutura e Operacao

- GitHub Actions para execucao agendada do worker
- Vercel para hospedagem do frontend estatico
- Backend Python separado para API publica

## Estrutura do Repositorio

- `frontend/`: aplicacao web, build e assets do cliente
- `backend/`: API, worker, regras de negocio, testes e dados
- `docs/`: arquitetura, planos de execucao e relatorios tecnicos
- `presentation/`: material estatico de apresentacao
- `.github/`: automacoes de CI/CD

## Convencoes de Repositorio

- Segredos nao devem ser commitados; use variaveis de ambiente.
- O arquivo `backend/config.yaml` deve permanecer com placeholders publicos.
- Arquivos locais, caches, builds e `.env` ja estao protegidos pelo `.gitignore`.
- Quebra de linha padrao do repositorio: LF, definida em `.gitattributes` e `.editorconfig`.

## Setup Local

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py --web
```

O backend sobe por padrao em `http://127.0.0.1:8000`.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

O frontend usa proxy local para o backend em `http://127.0.0.1:8000`.

## Configuracao

- Forneca credenciais reais por variaveis de ambiente do sistema, shell ou pipeline.
- O template de referencia para variaveis esta em `backend/.env.example`.
- A aplicacao le as variaveis diretamente do processo; se voce optar por `.env`, carregue-o externamente antes de iniciar o backend.

Variaveis esperadas:

- `GOOGLE_MAPS_API_KEY`
- `HERE_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_KEY` (compatibilidade temporaria)
- `AUTH_LOCAL_ENABLED`
- `AUTH_LOCAL_USERNAME`
- `AUTH_LOCAL_PASSWORD`
- `AUTH_LOCAL_SESSION_SECRET`
- `AUTH_COOKIE_SECURE`

## Dados Publicos Versionados

Os arquivos abaixo sao mantidos intencionalmente no repositório publico:

- `backend/data/rotas.json`
- `backend/data/favoritos.json`

Eles representam a base publica/operacional assumida para este projeto.

## GitHub Actions — Comportamento de Commit

> **Atencao:** um run do GitHub Actions usa o commit que estava no topo da branch **no momento em que o run foi disparado** (schedule ou `workflow_dispatch`), nao necessariamente o commit mais recente.
>
> Se voce fizer push de um novo commit e acionar o workflow antes que o GitHub processe o push, o run ainda ira executar o commit anterior.
>
> **Regra pratica:** apos um push, espere a aba **Actions** mostrar o SHA correto no cabecalho do run antes de interpretar os logs. Para forcar o commit mais recente, acione **Run workflow** manualmente *depois* de confirmar que o push foi recebido pelo GitHub.

## Fluxo Git Recomendado

1. Criar branch a partir de `main`.
2. Fazer mudancas pequenas e coerentes.
3. Validar localmente backend/frontend antes de abrir PR.
4. Commitar com mensagem objetiva e escopo claro.
5. Subir para o remote (`git push`) e aguardar confirmacao no GitHub.
6. Acionar o workflow manualmente somente apos o push estar visivel no repositorio remoto.

## Proximos Passos Naturais

- Configurar o remote do GitHub e publicar a branch `main`.
- Validar o workflow em `.github/workflows/monitor_dinamico.yml`.
- Fazer o cutover de deploy com backend publico + frontend via Vercel.
