# API e Operacao

Este documento resume o contrato operacional real do sistema.

## Superficie HTTP

### Publico

| Metodo | Rota | Objetivo |
| --- | --- | --- |
| `GET` | `/healthz` | health check |
| `POST` | `/auth/login` | cria sessao local |
| `POST` | `/auth/logout` | encerra sessao |
| `GET` | `/auth/session` | verifica sessao atual |
| `GET` | `/consultar` | consulta livre por origem/destino |
| `GET` | `/exportar/excel` | exporta consulta livre em `.xlsx` |
| `GET` | `/exportar/csv` | exporta consulta livre em `.csv` |
| `GET` | `/consultar/exportar/excel` | alias legado |
| `GET` | `/consultar/exportar/csv` | alias legado |

### Protegido por cookie

| Metodo | Rota | Objetivo |
| --- | --- | --- |
| `GET` | `/rotas` | lista rotas corporativas |
| `GET` | `/rotas/{rota_id}` | detalhe de rota corporativa |
| `GET` | `/rotas/{rota_id}/snapshot` | ultimo snapshot salvo |
| `GET` | `/rotas/{rota_id}/consultar` | consulta detalhada em tempo real |
| `GET` | `/painel` | resumo agregado do ultimo ciclo |
| `GET` | `/painel/exportar/excel` | exporta painel em `.xlsx` |
| `GET` | `/painel/exportar/csv` | exporta painel em `.csv` |
| `GET` | `/favoritos` | favoritos + rotas predefinidas |
| `POST` | `/favoritos` | adiciona favorito |
| `DELETE` | `/favoritos` | remove favorito |
| `GET` | `/cache/info` | diagnostico do cache |
| `DELETE` | `/cache` | limpeza manual do cache |

## Como o frontend consome a API

- o cliente web usa sempre `"/api/*"` como base;
- em producao, o `vercel.json` reescreve `"/api/:path*"` para o backend publico;
- em dev, o `vite.config.ts` faz proxy local de `"/api/*"` para `http://127.0.0.1:8000`.

## Origem dos dados

### Painel

- fonte principal: Supabase;
- comportamento: le o ultimo ciclo e os `snapshots_rotas`;
- finalidade: resposta rapida e consistente para visao executiva.

### Consulta detalhada

- tenta snapshot primeiro para resposta inicial;
- depois busca dados completos em tempo real;
- combina Google Routes e HERE Traffic em paralelo.

## Worker agendado

Arquivo principal: [`../backend/workers/coletor.py`](../backend/workers/coletor.py)

Workflow: [`../.github/workflows/monitor_dinamico.yml`](../.github/workflows/monitor_dinamico.yml)

Comportamento atual:

- agenda horaria (`0 * * * *`);
- instala dependencias Python a partir de `backend/requirements.txt`;
- executa `python workers/coletor.py` em `backend/`;
- envia os relatorios Excel gerados como artifact do workflow.

## Exportacao

### Consulta livre

- `GET /exportar/excel`
- `GET /exportar/csv`

Parametros:

- `origem`
- `destino`
- `rodovia_logica` opcional

### Painel agregado

- `GET /painel/exportar/excel`
- `GET /painel/exportar/csv`

## Observabilidade basica

- `GET /healthz` para health check;
- `X-Request-ID` em todas as respostas do backend;
- middleware de logs com latencia, status e IP;
- handlers centralizados para `HTTPException` e falhas nao tratadas.

## Notas de seguranca

- auth local e adequada apenas como camada inicial de protecao;
- credenciais placeholder bloqueiam a autenticacao automaticamente quando `AUTH_LOCAL_ENABLED=true`;
- o worker usa credenciais privilegiadas do Supabase e deve continuar isolado via GitHub Secrets.
