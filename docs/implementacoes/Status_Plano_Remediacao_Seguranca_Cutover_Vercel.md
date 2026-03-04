# Status do Plano de Remediacao de Seguranca e Cutover Vercel

## Objetivo

Registrar o plano consolidado, o que ja foi implementado no workspace e os proximos passos para concluir o cutover com seguranca.

## Atualizacao recente (04/03/2026)

- `backend/core/auth_local.py` foi endurecido:
  - cookie de sessao saiu de valor legivel com secret para token HMAC `username|timestamp|assinatura`
  - validacao agora usa `hmac.compare_digest()` e expiracao de 24h
- `backend/core/config_loader.py` agora marca `blocked_due_to_placeholders` e desabilita auth automaticamente quando `password` ou `session_secret` ainda estao em placeholder.
- `backend/web/app.py` passou a retornar `503` quando a auth for bloqueada por configuracao insegura, evitando reabrir endpoints "protegidos" por acidente.
- `/favoritos` (GET/POST/DELETE) e `/cache` (`GET /cache/info`, `DELETE /cache`) foram protegidos com `Depends(verificar_autenticacao)`.
- Validacao executada apos a remediacao:
  - `python -m pytest tests/test_auth_local.py tests/test_config_loader.py tests/test_web_app.py tests/test_web_app_incremento1.py`
  - resultado: 36 testes aprovados

## Referencia de plano

- Documento base de deploy: `docs/implementacoes/Plano_Deploy_Vercel_Substituicao_Projeto.md`
- Escopo adotado: aplicar remediacoes no codigo real, manter frontend com rotas relativas e usar backend FastAPI publico separado com proxy reverso pela Vercel.

## Resumo do plano

1. Higienizar o repositorio antes do primeiro ciclo Git.
2. Centralizar configuracao server-side com prioridade para variaveis de ambiente.
3. Remover segredos de arquivo versionado.
4. Corrigir backend, worker e GitHub Actions para deploy externo e coleta consistente.
5. Adicionar `vercel.json` na raiz para build e rewrites.
6. Validar backend externo, preview da Vercel e somente depois promover para producao.
7. Adiar `security-ownership-map` ate existir repositorio Git com historico util.

## O que foi feito

### Skills instaladas

- `security-best-practices`
- `security-ownership-map`
- `security-threat-model`

Observacao:
- As skills foram instaladas no ambiente do Codex, mas exigem restart da sessao para ficarem ativas como skills utilizaveis.

### Arquivos criados

- `backend/core/config_loader.py`
- `.gitignore`
- `vercel.json`
- `Monitoramento_Dinamico-threat-model.md`
- `security_best_practices_report.md`
- `security_ownership_map_status.md`
- `backend/tests/test_config_loader.py`
- `backend/tests/test_coletor.py`

### Arquivos alterados

- `backend/main.py`
- `backend/core/auth_local.py`
- `backend/storage/database.py`
- `backend/workers/coletor.py`
- `backend/web/app.py`
- `backend/requirements.txt`
- `backend/config.yaml`
- `.github/workflows/monitor_dinamico.yml`
- `backend/tests/test_auth_local.py`
- `backend/tests/test_web_app.py`
- `backend/tests/test_web_app_incremento1.py`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/index.html`
- `frontend/README.md`

### Arquivos removidos

- `package-lock.json` da raiz (placeholder vazio)

### Implementacoes concluidas

- Criado loader unico de configuracao com `config.yaml` + overrides por ambiente:
  - `GOOGLE_MAPS_API_KEY`
  - `HERE_API_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `SUPABASE_KEY` (fallback temporario)
  - `AUTH_LOCAL_ENABLED`
  - `AUTH_LOCAL_USERNAME`
  - `AUTH_LOCAL_PASSWORD`
  - `AUTH_LOCAL_SESSION_SECRET`
  - `AUTH_COOKIE_SECURE`
- `backend/config.yaml` foi saneado e deixou de conter segredos reais.
- `httpx` foi adicionado em `backend/requirements.txt`.
- O worker passou a usar o loader compartilhado e a chamar `init_supabase(config)` antes da persistencia.
- O backend web passou a usar o loader compartilhado no startup.
- Foi adicionado `GET /healthz` sem autenticacao.
- O cookie de sessao continua com o mesmo nome e agora respeita `AUTH_COOKIE_SECURE`.
- O cookie de sessao local deixou de expor o secret e passou a usar assinatura HMAC com expiracao.
- O backend agora diferencia:
  - auth explicitamente desabilitada (`enabled=false`) para modo legado
  - auth bloqueada por placeholders (`blocked_due_to_placeholders=true`) com falha fechada (`503`)
- O workflow do GitHub Actions foi corrigido para o layout real (`backend/`).
- Foi criado `vercel.json` na raiz com:
  - `installCommand`
  - `buildCommand`
  - `outputDirectory`
  - rewrites para `/auth`, `/painel` e `/rotas`
  - fallback final de SPA para `index.html`
- A identidade local do frontend foi normalizada:
  - nome do pacote para `monitoramento-dinamico-frontend`
  - titulo HTML para `Monitoramento Dinamico`
  - README deixou de usar o nome placeholder como nome principal do app
- Foi gerado um threat model inicial em `Monitoramento_Dinamico-threat-model.md`.

## Validacoes executadas

### Backend

Comando executado em `backend`:

```bash
python -m pytest tests/test_config_loader.py tests/test_auth_local.py tests/test_web_app_incremento1.py tests/test_coletor.py
```

Resultado:
- 21 testes aprovados

Cobertura adicionada:
- precedencia de variaveis de ambiente no loader
- fallback legado de `SUPABASE_KEY`
- normalizacao booleana
- cookie com e sem `Secure`
- `GET /healthz`
- ordem de bootstrap do worker

### Frontend

Comando executado em `frontend`:

```bash
npm run build
```

Resultado:
- build de producao concluido com sucesso
- metadados do frontend atualizados sem quebrar a pipeline de build

## Pendencias

- Este diretorio ainda nao e um repositorio Git.
- `security-ownership-map` ainda nao foi executada por falta de `.git` e historico util.
- O host em `vercel.json` esta como placeholder operacional:
  - `https://monitoramento-dinamico-api.onrender.com`
- Ainda nao houve deploy real do backend externo.
- Ainda nao houve preview deploy na Vercel com validacao ponta a ponta.
- As chaves anteriormente expostas em `backend/config.yaml` precisam ser rotacionadas fora do codigo.

## Proximos passos

1. Reiniciar o Codex para ativar as skills instaladas na sessao.
2. Confirmar a URL real do backend externo e atualizar `vercel.json` se necessario.
3. Publicar o backend FastAPI no host escolhido (padrao: Render) com `backend` como raiz, `requirements.txt` e health check em `/healthz`.
4. Configurar as variaveis de ambiente no backend externo:
   - `GOOGLE_MAPS_API_KEY`
   - `HERE_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `AUTH_LOCAL_ENABLED`
   - `AUTH_LOCAL_USERNAME`
   - `AUTH_LOCAL_PASSWORD`
   - `AUTH_LOCAL_SESSION_SECRET`
   - `AUTH_COOKIE_SECURE=true`
5. Rotacionar todas as credenciais que ja estiveram em arquivo versionado.
6. Registrar as configuracoes atuais do projeto existente na Vercel antes do cutover.
7. Conectar o projeto atual da Vercel a esta base de codigo e gerar um preview deployment.
8. Validar no preview:
   - login
   - `GET /auth/session`
   - `GET /painel`
   - `GET /rotas/R01/consultar`
   - hard refresh em `/painel`
   - hard refresh em `/consulta?rota_id=R01`
9. Executar manualmente o workflow do GitHub Actions e confirmar gravacao de pelo menos 1 novo ciclo no Supabase.
10. Somente apos preview e coleta validos, promover para producao.
11. Migrar ou preservar o historico Git do repositorio antigo antes de iniciar um repositorio novo aqui.
12. Depois que houver Git com historico util, executar `security-ownership-map`.

## Observacoes operacionais

- O uso de `SUPABASE_SERVICE_ROLE_KEY` e o padrao novo. `SUPABASE_KEY` ficou apenas como compatibilidade temporaria.
- O frontend nao foi alterado para `VITE_API_BASE_URL`; ele continua com rotas relativas por design.
- O warning atual de FastAPI e apenas deprecacao de `@app.on_event("startup")`; nao bloqueia a execucao atual.
