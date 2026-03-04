# Fase 0 - Decisao Arquitetural Consolidada

## Objetivo desta decisao

Transformar as respostas do questionario fechado em uma direcao tecnica executavel para a estrutura inicial do projeto.

---

## Decisao Central do Produto

O produto da primeira entrega sera **hibrido**, com dois fluxos complementares:

1. **Painel de monitoramento continuo** como interface principal de operacao.
2. **Consulta on-demand por rota individual** como mecanismo de checagem de fatos e validacao pontual de trafego em tempo real.

Em termos de prioridade de negocio:

- o **frontend principal** representa o monitoramento continuo;
- o **Projeto Zero** sera o modulo de validacao de acuracia e consulta detalhada.

---

## Respostas Consolidadas

## Q01. Produto principal da primeira entrega

**Decisao:** modelo hibrido.

Interpretacao executavel:

- o painel continuo e o fluxo principal;
- a consulta on-demand entra desde o inicio como modulo de suporte operacional.

## Q02. Visao Geral entra na primeira versao?

**Decisao:** Sim, como modulo simples complementar.

## Q03. Backend oficial

**Decisao:** `projeto_zero_separado`.

Implicacao:

- toda a consolidacao parte dele;
- o legado nao sera a base de execucao principal.

## Q04. Papel do `monitor-rodovias`

**Decisao:** referencia funcional e fonte de regras legadas.

Implicacao:

- reutilizar apenas o que agrega valor;
- evitar manter logica critica duplicada.

## Q05. Supabase entra agora?

**Decisao:** Sim, completo.

Escopo assumido:

- persistencia,
- base de integracao para autenticacao,
- e base de integracao para realtime.

## Q06. Autenticacao na primeira entrega

**Decisao:** Sim, autenticacao simples interna.

Interpretacao:

- controle de acesso para uso operacional interno;
- nao exige, nesta fase, um sistema complexo de perfis e administracao;
- a implementacao inicial sera **temporaria local**, mesmo com Supabase presente na arquitetura.

## Q07. Fontes de dados da primeira versao

**Decisao:** `HERE + Google`.

Implicacao:

- `TomTom` fica fora do fluxo inicial;
- reduz complexidade na consolidacao.

## Q08. Frontend oficial inicial

**Decisao:** `Frontend/Criar frontend dinamico`.

Observacao:

- a interface podera ter ajustes de parametros, estrutura e UI/UX conforme a integracao exigir.

## Q09. Estrategia para o frontend novo

**Decisao:** primeiro design e adaptacao visual, depois integracao com a API real.

Interpretacao em duas etapas:

1. congelar a estrutura visual e o fluxo principal;
2. substituir mocks por integracao real.

## Q10. Papel do frontend novo

**Decisao:** base visual a ser adaptada para producao.

## Q11. Fonte oficial das rotas predefinidas

**Decisao:** `Automacao Monitaramento de rotas Logisticas/monitor-rodovias/rota_logistica.json`.

Implicacao:

- o cadastro corporativo oficial parte do legado;
- o backend canonico precisara consumir ou absorver esse arquivo.

## Q12. Favoritos x rotas corporativas

**Decisao:** ignorar favoritos nesta fase e focar apenas em rotas corporativas.

Implicacao:

- `favoritos` deixam de ser prioridade da primeira entrega.

## Q13. Waypoints obrigatorios (`via`)

**Decisao normalizada:** Sim, mas apenas para rotas predefinidas.

Base para normalizacao:

- hoje voce utiliza 20 rotas predefinidas;
- a expansao para outros cenarios fica para fase futura.

## Q14. Contrato principal da aplicacao

**Decisao:** ambos desde a primeira entrega.

Portanto teremos:

- contrato detalhado por consulta individual;
- contrato agregado para painel multi-rotas.

## Q15. Exportacao na primeira entrega

**Decisao:** exportacao de rota individual + visao geral.

## Q16. Ambiente alvo inicial

**Decisao:** execucao local / servidor interno.

## Q17. Historico de ciclos e comparacao temporal

**Decisao:** nao entram agora.

Interpretacao:

- foco em decisao operacional em tempo real;
- mesmo com Supabase presente, o historico nao e a prioridade funcional inicial.

## Q18. Criterio principal de sucesso da primeira entrega

**Decisao:** entregar painel consolidado multi-rotas em operacao.

Implicacao:

- a consulta on-demand e suporte critico,
- mas o sucesso principal sera medido pelo painel funcionando.

## Q19. O que fica fora da primeira entrega

**Decisao:** login complexo, realtime robusto de producao e deploy cloud completo.

Normalizacao tecnica do seu item:

- manter autenticacao simples interna;
- evitar expandir para infraestrutura cloud completa nesta fase.

## Q20. Usuario primario

**Decisao de trabalho:** operacao logistica / torre de monitoramento.

Base:

- voce marcou como indiferente;
- para decisao arquitetural, precisamos de uma referencia de prioridade.

---

## Estrutura Inicial Aprovada

## 1. Backend canonico

`projeto_zero_separado` sera a base principal.

Ele precisara ser adaptado para:

- consumir as 20 rotas de `rota_logistica.json`,
- suportar o contrato agregado do painel,
- integrar autenticacao interna temporaria e Supabase,
- e manter o fluxo on-demand detalhado como modulo de checagem.

## 2. Legado

`monitor-rodovias` deixa de ser o centro da execucao e passa a fornecer:

- regras de negocio,
- cadastro de rotas,
- referencias de operacao,
- e trechos de implementacao que valha reaproveitar.

## 3. Frontend oficial

`Frontend/Criar frontend dinamico` sera a interface oficial.

Ele sera adaptado em duas ondas:

1. consolidacao de estrutura visual e fluxo do painel;
2. integracao com os contratos reais do backend.

Regras complementares definidas:

- o painel principal abrira diretamente com as 20 rotas predefinidas;
- os filtros iniciais ja existentes no frontend serao preservados como base;
- a UI/UX pode ser ajustada conforme a integracao real exigir.

## 4. Dados oficiais

As 20 rotas predefinidas em `rota_logistica.json` serao a fonte de verdade operacional inicial.

Nesta fase:

- sem favoritos de usuario;
- sem rotas livres arbitrarias como foco principal;
- com consulta on-demand usada para validacao e checagem de fatos;
- com atalho para reutilizar rapidamente qualquer uma das 20 rotas corporativas.

## 5. Fontes de trafego

O produto inicial usara:

- `HERE` como base de geometria, incidentes e fluxo;
- `Google` como apoio de duracao e atraso.

`TomTom` fica fora do escopo inicial de consolidacao.

---

## Escopo Funcional da Primeira Entrega

## Dentro do escopo

1. Painel de monitoramento continuo de rotas predefinidas.
2. Consulta on-demand por rota individual.
3. Suporte a waypoints nas 20 rotas corporativas.
4. Visao geral multi-rotas.
5. Exportacao da visao geral.
6. Exportacao da consulta individual.
7. Integracao com Supabase.
8. Autenticacao interna simples.
9. Frontend novo como interface principal.

## Fora do escopo

1. Favoritos de usuario.
2. TomTom.
3. Expansao irrestrita para rotas customizadas como foco principal.
4. Historico analitico e comparacao temporal como produto principal.
5. Deploy cloud completo nesta fase.
6. Sistema complexo de perfis e gestao de usuarios.

---

## Tensoes e Ajustes Necessarios

Existem algumas combinacoes nas respostas que exigem cuidado de implementacao:

## 1. Supabase completo vs ambiente local/interno

Voce decidiu por Supabase completo (`Q05`) e, ao mesmo tempo, por ambiente inicial local/interno (`Q16`).

Interpretacao tecnica:

- a infraestrutura de dados pode existir desde ja;
- a entrega inicial nao depende de um deploy cloud completo para usuarios externos.
- o uso inicial pode ser local/interno mesmo com o backend preparado para integrar Supabase.

## 2. Realtime vs item fora do escopo

Voce marcou Supabase com realtime, mas tambem indicou que o escopo inicial nao deve tentar fechar toda a infraestrutura final.

Interpretacao tecnica:

- o projeto pode preparar a estrutura para realtime;
- mas o objetivo da primeira entrega nao deve depender de um hardening completo dessa camada;
- o realtime sera incrementado **depois** que o painel base estiver estavel, inclusive para evitar consumo desnecessario de API.

## 3. Supabase na arquitetura vs autenticacao temporaria local

Voce decidiu usar uma solucao temporaria local para autenticacao inicial.

Interpretacao tecnica:

- o controle de acesso do primeiro incremento nao depende de Supabase Auth;
- Supabase continua na arquitetura para persistencia e evolucao posterior;
- a migracao para autenticacao integrada pode acontecer depois, sem travar o painel base.

## 4. Frontend primeiro no design, depois integracao

Essa escolha e valida, mas cria risco de desalinhamento com o backend.

Diretriz:

- o design deve ser congelado rapidamente;
- a integracao com contrato real deve comecar logo em seguida;
- evitar prolongar o uso de mocks.

---

## Proximas Decisoes Operacionais Imediatas

A Fase 0 agora permite seguir para os proximos cortes estruturais:

1. Definir como `rota_logistica.json` sera incorporado ao backend canonico.
2. Definir os dois contratos oficiais:
   consulta individual e painel agregado.
3. Definir o modelo minimo de autenticacao interna temporaria.
4. Definir a estrutura inicial de paginas do frontend novo:
   painel principal, consulta detalhada e login.
5. Definir o que do Supabase entra funcionalmente ja no primeiro incremento:
   persistencia agora, auth depois e realtime depois.

---

## Decisoes Complementares Fechadas

As ultimas definicoes da Fase 0 ficaram assim:

1. A autenticacao simples interna inicial sera feita por uma **solucao temporaria local**.
2. O painel principal abrira **diretamente com as 20 rotas**; os filtros iniciais ja definidos no frontend permanecem como base.
3. A consulta on-demand tera **atalho para reutilizar as 20 rotas corporativas**, alem do fluxo de consulta detalhada.
4. O realtime **nao e requisito do primeiro incremento funcional**; ele sera incorporado logo depois que o painel base estiver estavel, para reduzir consumo desnecessario.

---

## Conclusao

A direcao da Fase 0 esta definida:

- **backend base:** `projeto_zero_separado`
- **frontend base:** `Frontend/Criar frontend dinamico`
- **cadastro oficial de rotas:** `rota_logistica.json` do legado
- **modelo funcional:** painel continuo + consulta on-demand
- **fontes iniciais:** HERE + Google
- **autenticacao inicial:** solucao temporaria local
- **realtime:** posterior ao painel base estavel
- **escopo principal:** colocar o painel multi-rotas em operacao, com o Projeto Zero como suporte de validacao

Com isso, a proxima etapa correta e montar a **estrutura tecnica do incremento 1**.
