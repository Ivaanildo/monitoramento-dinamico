Plano de Cutover para Vercel (Substituindo o projeto atual)
Resumo
O bundle do frontend já compila; o bloqueio para produção não é build, e sim infraestrutura e hardening.
Status em 2026-03-04: este repositório já tem `.git`, `.gitignore` e `vercel.json`; trate as menções abaixo sobre ausência desses itens como contexto histórico do plano original.
O frontend atual depende de /auth, /painel e /rotas em runtime; então a Vercel deve hospedar o frontend e fazer proxy para um backend Python público separado.
O backend e o worker ainda exigem validação operacional antes do cutover final: conferir o workflow monitor_dinamico.yml no layout atual, garantir inicialização correta do cliente Supabase no worker e manter `config.yaml` sem segredos reais.
Estratégia fechada: manter o mesmo projeto/domínio atual da Vercel, migrar a origem para este código, usar backend FastAPI separado (padrão: Render) e preservar no frontend as URLs relativas atuais via rewrites da Vercel.
Plano de execução
Preparar a raiz deste repositório como a origem oficial do projeto. Antes do primeiro commit, garantir `.gitignore`, excluir do versionamento frontend/node_modules, frontend/dist, server.out.log, server.err.log, diretórios virtuais e arquivos temporários, e remover qualquer lockfile vazio fora de `frontend/package-lock.json`.
Sanear segredos e endurecer a configuração. Esvaziar config.yaml para deixar só placeholders não sensíveis e implementar um único carregador de configuração reutilizado pelo backend web e pelo worker, com overlay explícito de variáveis de ambiente. O mapeamento padrão deve ser: GOOGLE_MAPS_API_KEY, HERE_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (com fallback temporário para SUPABASE_KEY), AUTH_LOCAL_ENABLED, AUTH_LOCAL_USERNAME, AUTH_LOCAL_PASSWORD, AUTH_LOCAL_SESSION_SECRET e AUTH_COOKIE_SECURE. Antes do cutover, rotacionar todas as chaves hoje gravadas em arquivo.
Corrigir o backend para hospedagem externa. Adicionar httpx a requirements.txt, criar GET /healthz sem autenticação para health check, e ajustar auth_local.py para usar secure=True quando AUTH_COOKIE_SECURE=true e manter secure=False no desenvolvimento local. O nome do cookie e as rotas atuais devem permanecer iguais.
Corrigir o worker de coleta para produção. No bootstrap de coletor.py, inicializar o cliente Supabase com a configuração carregada antes de chamar salvar_snapshot_agregado. O worker e a API de leitura devem usar a mesma fonte de segredos por environment. A chave usada no backend/worker deve ser server-side de escrita, não chave de cliente.
Corrigir o GitHub Actions para o layout real do repositório. Ajustar monitor_dinamico.yml para operar em backend/, não em Monitoramento_Dinamico/backend. O fluxo final deve usar requirements.txt, instalar dependências a partir de requirements.txt e executar o worker a partir de backend.
Publicar o backend fora da Vercel. Padrão adotado: criar um serviço FastAPI chamado monitoramento-dinamico-api em Render com raiz backend, instalação via requirements.txt, start command uvicorn web.app:app --host 0.0.0.0 --port $PORT e health check em /healthz. Configurar nesse serviço todas as variáveis do passo 2 e validar primeiro a URL HTTPS direta em /healthz.
Padronizar a camada Vercel dentro do repositório. Adicionar vercel.json na raiz do projeto, não dentro de frontend. Definir installCommand como cd frontend && npm ci, buildCommand como cd frontend && npm run build, outputDirectory como frontend/dist, e rewrites em dois grupos: rewrites de API para o backend público (/auth/*, /painel, /painel/*, /rotas/*) e um rewrite final de SPA para index.html. Não alterar api.ts nem as rotas relativas do frontend; o browser deve continuar chamando o mesmo origin.
Reusar o projeto atual da Vercel. Antes de editar qualquer coisa, registrar as configurações atuais (domínios, variáveis, build settings e último deployment saudável). Depois, reconectar o projeto existente à nova origem baseada neste repositório, com Root Directory na raiz do repositório. Os antigos VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY deixam de ser exigência desta versão; podem ficar temporariamente, mas devem ser removidos após validação para evitar confusão operacional.
Fazer o cutover em duas etapas. Primeiro gerar um deployment de preview e validar login, painel, consulta e hard refresh. Só depois promover para produção no mesmo projeto da Vercel. O deployment anterior deve ficar anotado como rollback imediato.
Encerrar a substituição só após estabilização. Depois do primeiro deploy estável, executar manualmente o workflow do GitHub Actions, confirmar a criação de um novo ciclo no Supabase e observar pelo menos um ciclo agendado completo antes de aposentar o fluxo antigo.
Interfaces, contratos e validação
Interface externa preservada no frontend: continuar usando POST /auth/login, GET /auth/session, GET /painel e GET /rotas/{rota_id}/consultar como rotas relativas. A mudança é de infraestrutura, não de contrato com o navegador.
Novo endpoint público no backend: GET /healthz, resposta 200, sem autenticação, usado para health check e verificação do deploy.
Novo contrato de configuração server-side: o backend deixa de depender de segredos hardcoded em config.yaml e passa a aceitar env vars como fonte primária. SUPABASE_SERVICE_ROLE_KEY vira a variável padrão de escrita; SUPABASE_KEY fica só como compatibilidade temporária.
Cookie de sessão: manter projeto_zero_session, manter SameSite=Lax, e tornar o flag Secure dependente de ambiente. Em produção ele deve sair como seguro para funcionar corretamente sob HTTPS na Vercel.
Critérios de aceitação obrigatórios:
npm run build em frontend continua verde.
O backend responde 200 em /healthz.
POST /auth/login passando pela URL da Vercel retorna 200 e entrega Set-Cookie.
GET /auth/session pela Vercel retorna autenticado após login.
GET /painel pela Vercel carrega sem 401.
GET /rotas/R01/consultar pela Vercel responde com payload real.
Recarregar manualmente /painel e /consulta?rota_id=R01 não gera 404, confirmando o rewrite de SPA.
Um run manual do workflow grava pelo menos 1 ciclo novo no Supabase.
Cenário de rollback: se qualquer teste de autenticação, rewrite ou coleta falhar, restaurar o deployment anterior da Vercel e manter o backend novo isolado até correção; o fluxo antigo não deve ser desligado antes disso.
Assunções e defaults
O novo repositório será público, com segredos mantidos exclusivamente fora do versionamento.
O mesmo projeto/domínio atual da Vercel será mantido.
A API ficará fora da Vercel e o host padrão adotado é Render; se outro host for usado depois, a única troca estrutural é o destino das rewrites.
O frontend continuará em modo de API relativa com proxy reverso; não será introduzido VITE_API_BASE_URL nesta etapa.
O deploy de produção só acontece depois de um preview validado.
As referências usadas para a forma de configuração da Vercel são as docs oficiais de Project Configuration e Rewrites: https://vercel.com/docs/project-configuration e https://vercel.com/docs/rewrites
