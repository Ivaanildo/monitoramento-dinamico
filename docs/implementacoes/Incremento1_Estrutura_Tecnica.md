# Incremento 1 - Estrutura Tecnica de Implementacao

## Objetivo do incremento

Colocar o **painel base multi-rotas** em operacao local/interna, usando:

- `projeto_zero_separado` como backend canonico,
- `Frontend/Criar frontend dinâmico` como frontend oficial,
- `rota_logistica.json` como fonte oficial das 20 rotas corporativas,
- autenticacao local temporaria,
- e consulta on-demand como modulo de checagem de fatos.

Neste incremento, o sistema precisa funcionar sem depender de:

- realtime obrigatorio,
- deploy cloud completo,
- favoritos de usuario,
- ou historico analitico como produto principal.

---

## Resultado esperado ao final do Incremento 1

Ao final deste incremento, o sistema deve permitir:

1. Login local simples para acesso ao painel.
2. Abertura direta do painel com as 20 rotas predefinidas.
3. Exibicao da visao geral com status consolidado por rota.
4. Clique ou acao rapida em qualquer rota para abrir a consulta detalhada.
5. Reuso rapido de uma rota corporativa no fluxo on-demand.
6. Exportacao da visao geral e da consulta individual.
7. Persistencia basica do snapshot atual preparada para Supabase, sem depender ainda de realtime.

---

## Escopo tecnico do Incremento 1

### Dentro do escopo

1. Backend para listar, consultar e detalhar as 20 rotas.
2. Normalizacao de `rota_logistica.json` para consumo interno.
3. Contrato de dados do painel e da consulta detalhada.
4. Frontend novo integrado com backend real.
5. Autenticacao local temporaria.
6. Persistencia basica no Supabase.
7. Exportacao funcional.

### Fora do escopo

1. Realtime funcional em producao.
2. Supabase Auth como auth oficial.
3. Historico analitico e comparacao temporal.
4. TomTom.
5. Cadastro dinamico de novas rotas pelo usuario.

---

## Arquitetura alvo do Incremento 1

```text
Frontend/Criar frontend dinâmico
  -> login local temporario
  -> painel principal (20 rotas)
  -> consulta detalhada por rota
  -> exportacoes
  -> chama API HTTP do projeto_zero_separado

projeto_zero_separado
  -> carrega rota_logistica.json do legado
  -> normaliza 20 rotas corporativas
  -> consulta HERE + Google por rota
  -> monta payload agregado do painel
  -> monta payload detalhado on-demand
  -> persiste snapshot atual (baseline para Supabase)
  -> expone endpoints para login local, painel e detalhe

Automação Monitaramento de rotas Logisticas/monitor-rodovias
  -> fonte de dados e referencia de regras
  -> nao sera a base principal de execucao
```

---

## Estrutura proposta por frente de trabalho

### Frente 1 - Integracao dos dados corporativos

#### Objetivo

Fazer o backend canonico consumir corretamente as 20 rotas de `rota_logistica.json`.

#### Fonte oficial

`Automação Monitaramento de rotas Logisticas/monitor-rodovias/rota_logistica.json`

#### Estrutura real do arquivo

O arquivo ja traz o que precisamos:

- `routes[]`
- `id`
- `origem.hub`, `origem.lat`, `origem.lng`
- `destino.hub`, `destino.lat`, `destino.lng`
- `rodovia_logica[]`
- `here.origin`
- `here.destination`
- `here.via[]`
- `waypoints_status.n_points`
- `waypoints_status.distance_km`
- `limite_gap_km`

#### Implementacao prevista

Criar um modulo novo no backend:

- `projeto_zero_separado/core/rotas_corporativas.py`

#### Responsabilidades desse modulo

1. Ler o arquivo legado.
2. Validar estrutura minima.
3. Normalizar o formato para uso interno.
4. Expor metodos para:
   - listar rotas
   - buscar rota por `id`
   - converter rota corporativa em parametros de consulta

#### Modelo interno recomendado

```json
{
  "id": "R01",
  "hub_origem": "Sao Paulo (Cajamar)",
  "hub_destino": "Pernambuco (Cabo)",
  "origem": "-23.333027,-46.823893",
  "destino": "-8.295446,-35.057952",
  "via": ["...!passThrough=true"],
  "rodovia_logica": ["BR-116", "BR-101"],
  "distance_km": 2565.7,
  "n_waypoints": 29,
  "limite_gap_km": 106
}
```

#### Criterio de aceite

- as 20 rotas devem carregar sem adaptacao manual;
- `R01` a `R20` devem estar acessiveis por `id`;
- `via` e `rodovia_logica` devem ser preservados integralmente.

---

### Frente 2 - Contratos de dados

#### Objetivo

Definir os dois contratos oficiais:

1. contrato agregado do painel
2. contrato detalhado da consulta individual

#### Contrato 1 - Painel agregado

Payload para carregar as 20 rotas no dashboard.

#### Nome recomendado

`PainelRotasResponse`

#### Estrutura recomendada

```json
{
  "consultado_em": "2026-03-03T12:00:00Z",
  "fonte": "cache|live",
  "total_rotas": 20,
  "resultados": [
    {
      "rota_id": "R01",
      "sigla": "BR-116 / BR-101",
      "nome": "Sao Paulo (Cajamar) -> Pernambuco (Cabo)",
      "trecho": "Sao Paulo (Cajamar) / Pernambuco (Cabo)",
      "status": "Intenso",
      "ocorrencia": "Colisao",
      "relato": "Resumo operacional curto",
      "hora_atualizacao": "2026-03-03T12:00:00Z",
      "confianca_pct": 90,
      "atraso_min": 15
    }
  ]
}
```

#### Contrato 2 - Consulta detalhada

Payload para abrir o detalhe da rota e servir de base para a checagem on-demand.

#### Nome recomendado

`ResultadoRotaDetalhado`

#### Base

Usar o `ResultadoRota` atual do `projeto_zero_separado` como contrato base, adicionando:

- `rota_id`
- `hub_origem`
- `hub_destino`
- `via_coords`

#### Contrato 3 - Auth local

#### Nome recomendado

`LocalAuthSession`

#### Estrutura recomendada

```json
{
  "authenticated": true,
  "username": "operacao",
  "mode": "local-temp"
}
```

#### Criterio de aceite

- o frontend deve conseguir operar sem inferencia de campos;
- os nomes de campos devem substituir os mocks atuais;
- o mesmo contrato deve servir para API, UI e exportacao.

---

### Frente 3 - Backend HTTP e servicos

#### Objetivo

Expandir `projeto_zero_separado` para atender o painel, o detalhe e a autenticacao local.

#### Arquivos principais a ajustar

- `projeto_zero_separado/web/app.py`
- `projeto_zero_separado/core/consultor.py`
- `projeto_zero_separado/report/excel_simple.py`

#### Arquivos novos recomendados

- `projeto_zero_separado/core/rotas_corporativas.py`
- `projeto_zero_separado/core/auth_local.py`
- `projeto_zero_separado/core/painel_service.py`

#### Responsabilidades por modulo

##### `core/rotas_corporativas.py`

- leitura e normalizacao de `rota_logistica.json`

##### `core/painel_service.py`

- montar a visao geral agregada
- transformar o resultado detalhado em resumo de painel
- encapsular refresh das 20 rotas

##### `core/auth_local.py`

- autenticar usuario local fixo
- emitir e validar sessao simples
- centralizar regra temporaria de acesso

#### Endpoints recomendados

##### Auth local

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/session`

##### Rotas corporativas

- `GET /rotas`
- `GET /rotas/{rota_id}`

##### Painel

- `GET /painel`
- `GET /painel/exportar/excel`
- `GET /painel/exportar/csv`

##### Consulta detalhada

- `GET /rotas/{rota_id}/consultar`
- `GET /consultar`
- `GET /consultar/exportar/excel`
- `GET /consultar/exportar/csv`

#### Regras de negocio do backend

1. O painel deve usar as 20 rotas do arquivo corporativo.
2. A consulta por `rota_id` deve reaproveitar `via` e `rodovia_logica`.
3. A consulta livre (`/consultar`) continua existindo.
4. O fluxo detalhado de uma rota corporativa e a consulta livre devem compartilhar o mesmo nucleo de consulta.
5. O cache deve continuar ativo para evitar consumo desnecessario de API.

#### Criterio de aceite

- o backend deve iniciar localmente com os novos endpoints;
- `/painel` deve retornar 20 resultados;
- `/rotas/R01/consultar` deve refletir `via` e `rodovia_logica` do arquivo oficial.

---

### Frente 4 - Autenticacao local temporaria

#### Objetivo

Proteger o painel com uma camada minima de acesso sem bloquear o desenvolvimento.

#### Estrategia

Usar autenticacao local simples, sem depender ainda de Supabase Auth.

#### Implementacao recomendada

Configurar credenciais locais em `config.yaml`:

```yaml
auth_local:
  enabled: true
  username: "operacao"
  password: "definir_localmente"
  session_secret: "trocar-em-dev"
```

#### Comportamento recomendado

1. `POST /auth/login` valida credenciais.
2. Backend cria sessao simples por cookie HTTP-only ou token assinado local.
3. Endpoints do painel exigem sessao valida.
4. Endpoints tecnicos ou de health podem permanecer abertos.

#### Observacao

Isso e temporario. O objetivo e:

- liberar a operacao interna agora;
- permitir migracao limpa para Supabase Auth depois.

#### Criterio de aceite

- usuario loga localmente;
- sem login, o frontend nao carrega o painel;
- com login, o painel carrega normalmente.

---

### Frente 5 - Persistencia basica e base para Supabase

#### Objetivo

Introduzir persistencia agora, sem transformar historico em dependencia funcional do painel.

#### Diretriz

O frontend nao deve depender de realtime neste incremento.

#### Estrategia recomendada

Persistir o **snapshot atual** do painel apos cada refresh completo das 20 rotas.

#### Estrutura de codigo recomendada

Criar uma camada nova no backend:

- `projeto_zero_separado/storage/database.py`
- `projeto_zero_separado/storage/repository.py`

#### Responsabilidades

1. Conectar ao Supabase PostgreSQL.
2. Persistir o snapshot agregado do painel.
3. Opcionalmente manter estrutura compativel com evolucao para historico depois.

#### Regra importante

- o painel deve continuar funcionando mesmo se a persistencia falhar;
- falha no Supabase deve gerar log, nao derrubar a resposta da API.

#### Criterio de aceite

- o backend consegue tentar persistir o snapshot;
- se houver falha de DB, a API ainda responde;
- a estrutura fica pronta para evolucao de auth/realtime no Incremento 2.

---

### Frente 6 - Frontend oficial

#### Objetivo

Transformar o frontend novo em interface funcional do produto.

#### Base atual

Hoje o frontend novo ainda esta mockado:

- `Frontend/Criar frontend dinâmico/src/app/App.tsx`
- `Frontend/Criar frontend dinâmico/src/data/mockData.ts`

#### Diretriz

Primeiro consolidar a estrutura visual.
Depois substituir os mocks por integracao real rapidamente.

#### Estrutura recomendada do frontend

Criar, no minimo:

- `src/app/pages/LoginPage.tsx`
- `src/app/pages/PainelPage.tsx`
- `src/app/pages/ConsultaPage.tsx`
- `src/app/services/api.ts`
- `src/app/services/auth.ts`
- `src/app/types/contracts.ts`

#### Fluxo de telas

##### 1. Login

- formulario simples
- autentica contra `POST /auth/login`

##### 2. Painel principal

- abre direto nas 20 rotas
- usa os filtros que ja existem como base
- carrega dados de `GET /painel`
- exibe status, ocorrencia, relato, hora de atualizacao

##### 3. Consulta detalhada

- abre por clique em uma rota do painel
- chama `GET /rotas/{rota_id}/consultar`
- tambem permite consulta livre por origem/destino

##### 4. Atalho de reuso

- o usuario pode reaproveitar rapidamente qualquer uma das 20 rotas corporativas no fluxo detalhado

#### Substituicoes planejadas

1. Remover dependencia de `mockData.ts` no fluxo principal.
2. Mapear `sigla`, `nome`, `trecho`, `status`, `ocorrencia`, `relato`, `hora_atualizacao` para a tabela do painel.
3. Reaproveitar os filtros ja desenhados, agora com dados reais.

#### Criterio de aceite

- o frontend inicia e autentica localmente;
- o painel carrega 20 rotas reais;
- clicar em uma rota abre o detalhe;
- os mocks deixam de ser a fonte primaria do fluxo principal.

---

### Frente 7 - Exportacao

#### Objetivo

Garantir que os dois fluxos entreguem saida operacional.

#### Fluxos obrigatorios

1. Exportacao da visao geral do painel.
2. Exportacao da consulta detalhada.

#### Backend

Reaproveitar e adaptar:

- `projeto_zero_separado/report/excel_simple.py`

#### Ajustes necessarios

1. Criar exportacao agregada alinhada ao contrato do painel.
2. Manter exportacao detalhada alinhada ao `ResultadoRotaDetalhado`.
3. Garantir nomes de colunas coerentes com a UI.

#### Criterio de aceite

- o usuario consegue exportar a lista das 20 rotas;
- o usuario consegue exportar o detalhe de uma rota consultada.

---

## Sequencia recomendada de implementacao

### Etapa 1 - Dados e contratos

1. Integrar `rota_logistica.json`
2. Criar modelo interno das rotas corporativas
3. Fechar contratos `PainelRotasResponse` e `ResultadoRotaDetalhado`

### Etapa 2 - Backend funcional

1. Criar endpoints de rotas e painel
2. Reusar `consultor.consultar` para rotas corporativas
3. Ajustar exportacoes

### Etapa 3 - Auth local

1. Implementar login local temporario
2. Proteger endpoints do painel

### Etapa 4 - Frontend real

1. Separar telas
2. Integrar login
3. Integrar painel
4. Integrar detalhe
5. Remover mocks do fluxo principal

### Etapa 5 - Persistencia basica

1. Adicionar camada de persistencia
2. Salvar snapshot agregado
3. Garantir degradacao segura em caso de falha

---

## Riscos do Incremento 1

1. Prolongar o uso de mocks e atrasar a integracao real do frontend.
2. Misturar regras do legado no backend novo sem encapsulamento.
3. Acoplar o painel ao Supabase antes de estabilizar a API local.
4. Tornar a autenticacao temporaria dificil de substituir depois.
5. Aumentar consumo de API se o cache nao for respeitado no refresh do painel.

---

## Regras de implementacao

1. Toda logica nova entra a partir de `projeto_zero_separado`.
2. O legado so fornece dados, referencia e, no maximo, trechos pontuais reaproveitados.
3. O frontend novo nao deve ganhar mais mocks estruturais.
4. Toda integracao deve passar pelos contratos definidos neste documento.
5. O realtime nao deve bloquear a entrega do painel base.

---

## Definicao de pronto do Incremento 1

O Incremento 1 estara pronto quando:

1. o usuario fizer login local e acessar o painel;
2. o painel carregar as 20 rotas reais de `rota_logistica.json`;
3. o usuario puder abrir a consulta detalhada de qualquer rota;
4. o backend usar `HERE + Google` com `via` e `rodovia_logica` nas rotas corporativas;
5. as exportacoes de painel e detalhe funcionarem;
6. a persistencia basica estiver acoplada sem quebrar a operacao;
7. e o sistema rodar localmente sem depender ainda de realtime.

---

## Proxima fase separada: implementacao e testes

Com este plano aprovado, a proxima acao correta e transformar o incremento em duas frentes operacionais distintas:

### Parte A - Implementacao

Produzir o **plano de execucao tecnico por arquivo**, definindo:

1. quais arquivos serao criados;
2. quais arquivos serao alterados;
3. em que ordem cada frente sera entregue;
4. qual sera o primeiro corte implementavel de ponta a ponta;
5. quais dependencias entre backend, frontend, auth, exportacao e persistencia precisam ser respeitadas.

#### Ordem 1 - Configuracao e fonte de dados

Arquivos a alterar:

- `projeto_zero_separado/config.yaml`
- `projeto_zero_separado/main.py`

Arquivos a criar:

- `projeto_zero_separado/core/rotas_corporativas.py`

Objetivo:

1. parar de depender de `favoritos.json` como fonte das rotas corporativas;
2. introduzir uma chave explicita de configuracao para o caminho de `rota_logistica.json`;
3. encapsular leitura, validacao e normalizacao em um modulo unico;
4. manter `main.py` apenas como ponto de bootstrap, sem espalhar regra de negocio.

Saida obrigatoria:

1. uma funcao de carga que retorne exatamente 20 rotas normalizadas;
2. busca por `rota_id`;
3. adaptador para converter rota corporativa em parametros compativeis com `consultor.consultar`.

#### Ordem 2 - Servico de painel e contratos internos

Arquivos a alterar:

- `projeto_zero_separado/core/consultor.py`

Arquivos a criar:

- `projeto_zero_separado/core/painel_service.py`

Objetivo:

1. separar a logica de agregacao do painel do arquivo HTTP;
2. transformar o resultado detalhado em resumo de painel;
3. padronizar os campos do contrato agregado antes da integracao do frontend;
4. manter `consultor.consultar` como nucleo unico da consulta, apenas com reuso orquestrado.

Saida obrigatoria:

1. funcao para listar o painel agregado;
2. funcao para consultar uma rota corporativa por `rota_id`;
3. funcao para converter resultado detalhado em linha de painel.

#### Ordem 3 - Camada HTTP e autenticacao local

Arquivos a alterar:

- `projeto_zero_separado/web/app.py`

Arquivos a criar:

- `projeto_zero_separado/core/auth_local.py`

Objetivo:

1. adicionar `POST /auth/login`, `POST /auth/logout` e `GET /auth/session`;
2. adicionar `GET /rotas`, `GET /rotas/{rota_id}` e `GET /rotas/{rota_id}/consultar`;
3. substituir gradualmente `/visao-geral` por `/painel` como endpoint canonico;
4. proteger endpoints de painel sem quebrar `/consultar`, `/cache` e rotas tecnicas ja existentes.

Saida obrigatoria:

1. sessao local simples baseada em cookie HTTP-only ou token assinado;
2. middleware ou dependencia de protecao para endpoints privados;
3. endpoints novos respondendo com os contratos finais do incremento.

#### Ordem 4 - Exportacao aderente aos novos contratos

Arquivos a alterar:

- `projeto_zero_separado/report/excel_simple.py`
- `projeto_zero_separado/web/app.py`

Objetivo:

1. alinhar a exportacao detalhada ao contrato final de `ResultadoRotaDetalhado`;
2. alinhar a exportacao agregada ao contrato de `PainelRotasResponse`;
3. manter reaproveitamento do modulo atual, sem criar um segundo exportador concorrente.

Saida obrigatoria:

1. exportacao agregada usando os mesmos campos exibidos no painel;
2. exportacao detalhada usando os mesmos campos consumidos na consulta.

#### Ordem 5 - Persistencia basica com degradacao segura

Arquivos a criar:

- `projeto_zero_separado/storage/__init__.py`
- `projeto_zero_separado/storage/database.py`
- `projeto_zero_separado/storage/repository.py`

Arquivos a alterar:

- `projeto_zero_separado/core/painel_service.py`

Objetivo:

1. persistir o snapshot agregado ao final de cada refresh completo;
2. manter a persistencia opcional e desacoplada do fluxo de resposta;
3. garantir que falha de banco gere log e nao indisponibilidade.

Saida obrigatoria:

1. interface unica de persistencia;
2. chamada de persistencia protegida por `try/except`;
3. log estruturado de falha sem interromper o retorno da API.

#### Ordem 6 - Frontend oficial sem mocks estruturais

Arquivos a alterar:

- `Frontend/Criar frontend dinâmico/src/main.tsx`
- `Frontend/Criar frontend dinâmico/src/app/App.tsx`
- `Frontend/Criar frontend dinâmico/src/data/mockData.ts`
- `Frontend/Criar frontend dinâmico/package.json`

Arquivos a criar:

- `Frontend/Criar frontend dinâmico/src/app/pages/LoginPage.tsx`
- `Frontend/Criar frontend dinâmico/src/app/pages/PainelPage.tsx`
- `Frontend/Criar frontend dinâmico/src/app/pages/ConsultaPage.tsx`
- `Frontend/Criar frontend dinâmico/src/app/services/api.ts`
- `Frontend/Criar frontend dinâmico/src/app/services/auth.ts`
- `Frontend/Criar frontend dinâmico/src/app/types/contracts.ts`

Objetivo:

1. trocar o fluxo monolitico atual de `App.tsx` por paginas separadas;
2. manter a base visual atual, mas retirar `ALL_ROADS` como fonte primaria;
3. integrar login, sessao, painel e consulta detalhada;
4. deixar `mockData.ts` apenas como apoio de desenvolvimento local ou remover do fluxo principal.

Saida obrigatoria:

1. `App.tsx` atuando como shell e roteador de estado;
2. `PainelPage.tsx` carregando `GET /painel`;
3. `ConsultaPage.tsx` carregando `GET /rotas/{rota_id}/consultar` e consulta livre;
4. `LoginPage.tsx` bloqueando acesso quando nao houver sessao.

### Parte B - Testes e validacao

Produzir um **plano de validacao por camada**, definindo:

1. testes de normalizacao de `rota_logistica.json`;
2. testes de contrato para `/rotas`, `/painel`, `/auth/session` e `/rotas/{rota_id}/consultar`;
3. testes de auth cobrindo acesso sem sessao e com sessao valida;
4. testes de integracao do frontend para login, carga do painel e abertura do detalhe;
5. testes de degradacao para falha de persistencia sem indisponibilizar a API;
6. validacao operacional de exportacao agregada e exportacao detalhada.

#### Camada 1 - Testes unitarios backend

Arquivos a criar:

- `projeto_zero_separado/tests/test_rotas_corporativas.py`
- `projeto_zero_separado/tests/test_painel_service.py`
- `projeto_zero_separado/tests/test_auth_local.py`

Arquivos a alterar:

- `projeto_zero_separado/tests/test_consultor.py`

Cobertura minima:

1. leitura e validacao da estrutura de `rota_logistica.json`;
2. normalizacao de `origem`, `destino`, `via`, `rodovia_logica`, `distance_km` e `limite_gap_km`;
3. resumo do painel derivado de um `ResultadoRota` detalhado;
4. emissao e validacao de sessao local;
5. preservacao do cache quando `rodovia_logica` variar.

#### Camada 2 - Testes de endpoint e contrato

Arquivos a alterar:

- `projeto_zero_separado/tests/test_web_app.py`

Arquivos a criar:

- `projeto_zero_separado/tests/test_exportacoes.py`

Cobertura minima:

1. `GET /rotas` retorna 20 rotas e expone `rota_id` ou `id` de forma consistente;
2. `GET /rotas/{rota_id}` retorna 404 para rota inexistente;
3. `GET /painel` retorna `total_rotas=20` e `resultados` aderente ao contrato;
4. `GET /rotas/{rota_id}/consultar` reaproveita `via` e `rodovia_logica`;
5. `GET /auth/session` reflete corretamente sessao ausente e sessao valida;
6. endpoints de exportacao retornam arquivo e content-type corretos.

#### Camada 3 - Testes de degradacao e resiliencia

Arquivos a criar:

- `projeto_zero_separado/tests/test_persistencia_snapshot.py`

Cobertura minima:

1. falha na camada `repository` nao impede resposta de `/painel`;
2. falha de persistencia gera log e nao muda status code de sucesso;
3. cache agregado continua funcional mesmo quando o banco falha.

#### Camada 4 - Testes de frontend

Arquivos a alterar:

- `Frontend/Criar frontend dinâmico/package.json`

Arquivos a criar:

- `Frontend/Criar frontend dinâmico/src/app/App.test.tsx`
- `Frontend/Criar frontend dinâmico/src/app/pages/LoginPage.test.tsx`
- `Frontend/Criar frontend dinâmico/src/app/pages/PainelPage.test.tsx`

Cobertura minima:

1. render inicial sem sessao redireciona para login;
2. login bem-sucedido libera acesso ao painel;
3. painel renderiza 20 linhas a partir do contrato da API;
4. clique em uma rota abre a consulta detalhada;
5. falha de API exibe estado de erro sem quebrar a tela.

Observacao:

1. como o frontend atual nao possui infraestrutura de teste declarada, esta etapa deve incluir a adicao de script de teste e dependencias de teste antes dos casos automatizados;
2. se isso ficar fora do corte inicial, manter ao menos um roteiro manual de smoke test com os mesmos cenarios.

### Primeiro corte recomendado

O primeiro corte implementavel deve entregar:

1. configuracao do caminho de `rota_logistica.json` em `config.yaml`;
2. criacao de `core/rotas_corporativas.py`;
3. criacao de `core/painel_service.py` com adaptador de contrato;
4. `GET /rotas`;
5. `GET /painel` com contrato final e sem persistencia obrigatoria;
8. ajuste de `tests/test_web_app.py` para validar 20 resultados e campos obrigatorios;
9. e `test_rotas_corporativas.py` cobrindo normalizacao basica.

---

## Status de Execução Final do Backend (Atualizado 2026-03-03)

O primeiro corte estrutural listado acima, bem como os componentes de **Autenticação Local** (Ordem 3) e **Exportação** (Ordem 4) foram finalizados e os testes automatizados correspondentes cobriram todo o processo. Para o panorama executivo do que já foi feito, consulte [docs/implementacoes/Contexto_Atual_Incremento1.md](./Contexto_Atual_Incremento1.md).

**Próximos Passos (Ordens 5 e 6):**
A API Base está congelada com 100% de testes passando. A sequência recomendada entra agora em:
* **Persistência do Supabase** (Ordem 5) e/ou
* **Integração Real do Frontend** (Ordem 6) substituindo os mocks dos componentes `PainelPage` e afins.
