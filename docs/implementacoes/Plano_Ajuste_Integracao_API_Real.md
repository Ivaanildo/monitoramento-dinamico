# Plano de Ajuste: Saída do Mock no Frontend e Alinhamento da Documentação

## Resumo

Objetivo: substituir o consumo de `mock_painel.json` pelo backend FastAPI real, corrigir o fluxo de autenticação por cookie e atualizar a documentação para refletir o estado real do repositório.

Fatos confirmados no repositório:
- O proxy do Vite já existe em [vite.config.ts](../../frontend/vite.config.ts).
- O frontend ainda está em modo mock em [api.ts](../../frontend/src/app/services/api.ts).
- O backend já expõe `/auth/login`, `/auth/session`, `/rotas/{rota_id}/consultar` e `/painel` em [app.py](../../backend/web/app.py).
- O backend espera login em JSON (`LoginIn`), enquanto o frontend atual envia `FormData` em [LoginPage.tsx](../../frontend/src/app/pages/LoginPage.tsx).
- Há risco real de o cookie não ser persistido porque `/auth/login` seta cookie no `Response` injetado, mas retorna um `JSONResponse` novo em [app.py](../../backend/web/app.py).

## Escopo e Resultado Esperado

- Trocar o frontend para usar a API real sem depender de arquivo estático local.
- Garantir que login gere sessão funcional por cookie e que as páginas protegidas parem de cair em `401` após autenticação válida.
- Preservar `generate_mock_frontend.py` como fallback offline, mas remover o mock do fluxo padrão de desenvolvimento.
- Atualizar a documentação para não instruir passos já concluídos e para incluir os desvios descobertos (payload de login e persistência do cookie).

## Mudanças de Implementação

### 1. Validar e congelar o padrão de desenvolvimento local

- Manter o proxy atual em [vite.config.ts](../../frontend/vite.config.ts) como padrão oficial de dev local.
- Não alterar rotas do proxy, exceto se houver divergência com a porta real do backend; o padrão assumido será `5173 -> 8000`.
- Tratar o passo “configurar proxy” na documentação como “verificar proxy existente”, não como trabalho pendente.

### 2. Restaurar a camada de API do frontend para modo real

- Substituir a implementação mock em [api.ts](../../frontend/src/app/services/api.ts).
- `api.get(url)` deve chamar `fetch(url, { credentials: "include" })`.
- `api.getConsulta(rota_id)` deve chamar `fetch(\`/rotas/${rota_id}/consultar\`, { credentials: "include" })`.
- Ambas devem:
  - lançar `Error("Unauthorized")` em `401`;
  - lançar `Error("HTTP " + status)` para outros erros HTTP;
  - retornar `res.json()` em sucesso.
- Não manter fallback automático para `mock_painel.json` em `api.ts`; o fallback continuará existindo apenas via script/manual, não no fluxo padrão.

### 3. Corrigir o contrato de login entre frontend e backend

- Ajustar [LoginPage.tsx](../../frontend/src/app/pages/LoginPage.tsx) para enviar JSON, não `FormData`.
- Implementação definida:
  - `method: "POST"`
  - `headers: { "Content-Type": "application/json" }`
  - `body: JSON.stringify({ username, password })`
  - `credentials: "include"` explícito para padronizar o comportamento de sessão.
- Manter o redirecionamento para `/painel` após `200 OK`.
- Manter a mensagem de erro em credenciais inválidas quando `!res.ok`.

### 4. Corrigir a emissão do cookie no backend

- Ajustar [app.py](../../backend/web/app.py) no endpoint `/auth/login` para que o cookie realmente seja retornado ao cliente.
- Implementação definida:
  - criar o payload de sucesso no mesmo objeto de resposta que receberá `set_cookie`, ou
  - criar um `JSONResponse`, chamar `auth_local.criar_sessao` sobre esse objeto e então retorná-lo.
- Não usar o padrão atual “setar cookie no `response` injetado e retornar outro `JSONResponse`”.
- Aplicar a mesma regra ao logout, se necessário, para garantir que `delete_cookie` atue sobre a resposta efetivamente retornada.
- Não alterar o nome do cookie (`projeto_zero_session`) nem os flags atuais em [auth_local.py](../../backend/core/auth_local.py): `httponly=True`, `samesite="lax"`, `secure` desabilitado em dev.

### 5. Validar o consumo dos campos ricos na consulta

- Confirmar que [ConsultaPage.tsx](../../frontend/src/app/pages/ConsultaPage.tsx) já consome os campos completos do backend sem necessidade de mudança estrutural.
- Validar especificamente:
  - `route_pts` para renderização da polilinha no mapa;
  - `incidentes` para lista e marcadores;
  - `velocidade_atual_kmh`, `velocidade_livre_kmh`, `jam_factor_avg`, `jam_factor_max`, `pct_congestionado`, `distancia_km`, `duracao_*`;
  - `link_waze` e `link_gmaps`.
- Só planejar mudança de frontend nessa página se o payload real divergir do shape já tipado em `ConsultaData`. O default assumido é que o shape já está compatível.

### 6. Remover o mock do fluxo padrão e preservar fallback offline

- Após a validação fim a fim, retirar `mock_painel.json` do fluxo padrão.
- Decisão de limpeza:
  - manter `generate_mock_frontend.py` no repositório (referência histórica do plano original);
  - remover `mock_painel.json` apenas depois da aceitação da integração;
  - se a equipe quiser fallback imediato durante transição, mover `mock_painel.json` para um artefato não referenciado pelo app, em vez de deixá-lo como dependência ativa.
- Não deixar nenhum `fetch("/mock_painel.json")` no código produtivo do frontend.

## Mudanças na Documentação

- Atualizar [Incremento3_Frontend_Mock_e_Integracao_API.md](Incremento3_Frontend_Mock_e_Integracao_API.md) para refletir o estado real.
- Substituir o “Passo 1” por “Validar proxy Vite já configurado”.
- Corrigir o “Passo 2” para incluir também ajuste de [LoginPage.tsx](../../frontend/src/app/pages/LoginPage.tsx), não só [api.ts](../../frontend/src/app/services/api.ts).
- Incluir uma nota explícita de que o backend espera login em JSON.
- Incluir uma nota explícita de que o endpoint `/auth/login` deve retornar o cookie na mesma resposta HTTP enviada ao navegador.
- Atualizar a ordem dos passos para esta sequência:
  1. Validar proxy já existente.
  2. Corrigir `/auth/login` para persistir cookie.
  3. Ajustar `LoginPage.tsx` para enviar JSON com credenciais.
  4. Restaurar `api.ts` para endpoints reais.
  5. Iniciar backend e validar `config.yaml`.
  6. Validar sessão via `/auth/session`, `/painel` e `/rotas/{rota_id}/consultar`.
  7. Remover `mock_painel.json` do fluxo padrão.
- Corrigir a introdução do arquivo para remover o texto duplicado que hoje aparece antes do título.

## Interfaces e Contratos Relevantes

- Endpoints públicos mantidos sem mudança de URL:
  - `POST /auth/login`
  - `GET /auth/session`
  - `GET /painel`
  - `GET /rotas/{rota_id}/consultar`
- Contrato de entrada definido para login:
  - JSON `{ "username": string, "password": string }`
- Contrato de sessão definido:
  - cookie HTTP-only `projeto_zero_session`
- Interface interna do frontend mantida:
  - `api.get(url: string)`
  - `api.getConsulta(rota_id: string)`
- Sem mudança planejada no shape esperado de `ConsultaData`, salvo correção se o backend real divergir durante a validação.

## Testes e Cenários de Aceitação

### Backend

- Atualizar ou adicionar teste em [test_web_app_incremento1.py](../../backend/tests/test_web_app_incremento1.py) para garantir que `POST /auth/login` com JSON válido:
  - retorna `200`;
  - inclui `Set-Cookie` com `projeto_zero_session`.
- Adicionar teste para `POST /auth/login` inválido:
  - retorna `401`;
  - não mantém sessão válida.
- Validar `GET /auth/session`:
  - sem cookie retorna `401` quando auth local está ativa;
  - com cookie válido retorna `200` e `authenticated: true`.

### Frontend

- Teste manual: login com credenciais corretas navega para `/painel` e não redireciona de volta para `/login`.
- Teste manual: abrir `/painel` após login carrega dados reais de `/painel`.
- Teste manual: abrir `/consulta?rota_id=R01` após login carrega payload real de `/rotas/R01/consultar`.
- Teste manual: quando o backend responder `401`, [PainelPage.tsx](../../frontend/src/app/pages/PainelPage.tsx) e [ConsultaPage.tsx](../../frontend/src/app/pages/ConsultaPage.tsx) redirecionam para `/login`.

### Dados ricos

- Confirmar que o mapa deixa de renderizar vazio quando `route_pts` vier populado.
- Confirmar que incidentes aparecem na lista lateral e no mapa quando `incidentes` vier populado.
- Confirmar que KPIs deixam de exibir `0` para campos de distância, velocidade e jam factor.

## Resumo do Status (Atualizado: Passo 4 - Concluído com Pivot Arquitetural)

As etapas iniciais de preparação e ajustes de segurança foram concluídas com sucesso. O frontend agora se autentica via JSON e os cookies de sessão são corretamente devolvidos e armazenados.
A etapa final de substituição do `mock_painel.json` foi além: em vez de fazer o frontend do `/painel` consumir APIs externas em tempo real, **recriamos a arquitetura original de pooling** isolando um *worker* e conectando o `/painel` diretamente ao banco de dados Supabase para leitura super-rápida.

**Ajuste considerado concluído com sucesso:**
- 🟢 Não há mais dependência funcional de `mock_painel.json` no frontend (arquivo apagado).
- 🟢 O login está agora enviando payload JSON.
- 🟢 O backend `/auth/login` retorna o `Set-Cookie` apropriado e o fluxo de persistência de sessão foi restaurado.
- 🟢 `/painel` e `/rotas/{rota_id}/consultar` respondem no proxy Vite real de desenvolvimento com a camada auth incluída.
- 🟢 A documentação em `Incremento3_Frontend_Mock_e_Integracao_API.md` foi revista.

## Assunções e Defaults

- O escopo inclui código e documentação.
- O ambiente de desenvolvimento continuará usando Vite com proxy local para evitar CORS.
- O backend continuará em `http://127.0.0.1:8000` durante o desenvolvimento.
- `auth_local` permanece como mecanismo temporário; não entra neste plano migrar para Supabase Auth.
- `generate_mock_frontend.py` será mantido como ferramenta offline, mas fora do fluxo padrão da aplicação.
