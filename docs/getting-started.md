# Getting Started

Guia pratico para levantar o projeto localmente sem depender de leitura dispersa.

## Pre-requisitos

- Python 3.11 ou superior
- Node.js 18 ou superior
- npm

## Estrutura minima

| Pasta | Conteudo |
| --- | --- |
| `backend/` | API FastAPI, worker, regras de negocio, testes |
| `frontend/` | SPA React/Vite |
| `backend/data/rotas.json` | cadastro das 20 rotas corporativas |
| `vercel.json` | contrato de deploy do frontend e rewrite de API |

## 1. Subir o backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py --web
```

Se quiser rodar testes backend:

```bash
cd backend
pytest
```

## 2. Subir o frontend

```bash
cd frontend
npm ci
npm run dev
```

O frontend roda em `http://127.0.0.1:5173` e encaminha `"/api/*"` para `http://127.0.0.1:8000`.

## Variaveis de ambiente

O backend carrega `config.yaml` e sobrescreve valores com env vars. O template base esta em [`../backend/.env.example`](../backend/.env.example).

| Variavel | Uso |
| --- | --- |
| `GOOGLE_MAPS_API_KEY` | consulta de tempo/rota via Google Routes |
| `HERE_API_KEY` | incidentes e fluxo via HERE |
| `SUPABASE_URL` | leitura/escrita de ciclos e snapshots |
| `SUPABASE_SERVICE_ROLE_KEY` | chave principal de persistencia |
| `SUPABASE_KEY` | fallback legado |
| `AUTH_LOCAL_ENABLED` | habilita auth local por cookie |
| `AUTH_LOCAL_USERNAME` | usuario do login local |
| `AUTH_LOCAL_PASSWORD` | senha do login local |
| `AUTH_LOCAL_SESSION_SECRET` | segredo da sessao |
| `AUTH_COOKIE_SECURE` | cookie seguro em ambiente HTTPS |

## URLs uteis

| URL | Finalidade |
| --- | --- |
| `http://127.0.0.1:8000/healthz` | health check |
| `http://127.0.0.1:8000/docs` | Swagger UI do FastAPI |
| `http://127.0.0.1:8000/redoc` | ReDoc do FastAPI |
| `http://127.0.0.1:5173` | frontend em dev |

## Fluxo local recomendado

1. Exportar as variaveis necessarias no shell.
2. Subir o backend.
3. Validar `GET /healthz` e `GET /docs`.
4. Subir o frontend.
5. Entrar no painel ou abrir a consulta detalhada a partir do grid.

## Observacoes operacionais

- sem chaves de API, o backend sobe, mas varias consultas retornam sem fontes disponiveis;
- sem Supabase configurado, o painel agregado retorna vazio;
- se `AUTH_LOCAL_ENABLED=true` for usado com placeholders, o `config_loader` bloqueia a autenticacao por seguranca.
