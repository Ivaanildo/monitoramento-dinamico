# Oneshoot v2 - Revisao Critica e Plano Estruturado

## Diagnostico Critico do Estado Atual

O plano inicial nao estava formalizado de forma operacional. Sem um documento estruturado, o projeto fica sem direcao clara de execucao.

### Principais problemas identificados

1. Nao ha objetivo definido com precisao.
2. Nao ha escopo claro entre os tres blocos do workspace:
   `Automacao Monitaramento de rotas Logisticas`, `projeto_zero_separado` e `Frontend/Criar frontend dinamico`.
3. Nao ha criterio de sucesso.
4. Nao ha sequenciamento tecnico.
5. Nao ha definicao de entregaveis.
6. Nao ha mapeamento de riscos, dependencias ou validacao.

### Consequencia pratica

Sem estrutura minima, a execucao tende a gerar retrabalho, integracao fragil, divergencia entre backend e frontend e manutencao de logicas duplicadas.

## Leitura Tecnica do Contexto Atual

Com base no workspace atual, ja existe material suficiente para um plano realista:

- `projeto_zero_separado` ja contem o nucleo mais maduro do produto:
  backend Python, FastAPI, consulta on-demand, cache, exportacao, logs e documentacao tecnica.
- `projeto_zero_separado/docs/PLANO_CORRECAO_ROTAS.md` mostra que parte critica da geometria e dos waypoints ja foi tratada.
- `Automacao Monitaramento de rotas Logisticas` parece concentrar a base legada e conhecimento operacional.
- `Frontend/Criar frontend dinamico` contem um frontend Vite/React que pode virar a camada visual consolidada.

Conclusao: o caminho correto nao e recomecar, e sim consolidar, reduzir duplicidade e definir uma linha unica de produto.

## Objetivo Revisado

Consolidar o projeto em uma unica solucao operacional para consulta e monitoramento de rotas logisticas, com:

- um backend canonico,
- um contrato de dados unico,
- um frontend integrado,
- e um fluxo de validacao que preserve a confiabilidade das rotas criticas.

## Principios do Plano

1. Eleger uma fonte de verdade por camada.
2. Preservar o que ja funciona antes de expandir.
3. Reduzir retrabalho entre legado, backend novo e frontend.
4. Tratar integracao como produto, nao como adaptacao improvisada.
5. Validar rotas criticas com criterios objetivos.

## Plano Estruturado

## Fase 0 - Alinhamento e Corte de Escopo

### Objetivo

Definir exatamente qual produto sera entregue nesta iteracao.

### Acoes

1. Escolher o backend canonico: usar `projeto_zero_separado` como base principal.
2. Definir o papel da pasta `Automacao Monitaramento de rotas Logisticas`:
   fonte de regras legadas, datasets, rotas fixas e referencia funcional.
3. Definir o papel de `Frontend/Criar frontend dinamico`:
   nova interface oficial, desde que respeite o contrato do backend.
4. Congelar o escopo da primeira entrega:
   consulta de rota, visualizacao no mapa, favoritos, exportacao e suporte a waypoints obrigatorios.

### Entregavel

Documento curto de decisao arquitetural com:

- fonte de verdade por modulo,
- funcionalidades dentro e fora do escopo,
- e criterio de aceite da primeira entrega.

### Criterio de saida

Nao pode restar duvida sobre qual codigo sera mantido, integrado ou descartado.

## Fase 1 - Baseline Tecnico e Inventario

### Objetivo

Mapear o que existe e identificar sobreposicoes.

### Acoes

1. Inventariar endpoints, formatos JSON, dependencias e fluxos de execucao do backend atual.
2. Comparar as regras de negocio da automacao legada com o backend `projeto_zero_separado`.
3. Listar pontos de duplicidade:
   geocodificacao, calculo de status, rotas predefinidas, exportacao, logs e cache.
4. Registrar lacunas de integracao entre backend e frontend:
   campos ausentes, nomes inconsistentes, estruturas nao normalizadas.

### Entregavel

Matriz de consolidacao com tres colunas:

- manter,
- adaptar,
- remover.

### Criterio de saida

Toda funcionalidade relevante deve ter um destino claro.

## Fase 2 - Contrato de Dominio e API

### Objetivo

Criar um contrato unico e estavel para o produto.

### Acoes

1. Formalizar `ResultadoRota` como contrato principal.
2. Padronizar campos obrigatorios e opcionais:
   status, metricas, incidentes, `route_pts`, `flow_pts`, `via_coords`, erros e metadados.
3. Definir versao de API e regras de compatibilidade.
4. Separar claramente:
   dados de consulta, dados de visualizacao e dados de exportacao.
5. Criar exemplos de payload para:
   rota simples, rota com waypoints, falha parcial de fonte e cache hit.

### Entregavel

Especificacao de API em Markdown ou OpenAPI enxuto.

### Criterio de saida

Frontend e backend passam a integrar por contrato, nao por tentativa e erro.

## Fase 3 - Consolidacao do Backend

### Objetivo

Eliminar ambiguidade tecnica e endurecer a base operacional.

### Acoes

1. Centralizar a logica em `projeto_zero_separado`.
2. Incorporar, de forma controlada, apenas as regras do legado que ainda agregam valor.
3. Revisar o fluxo de waypoints obrigatorios para garantir:
   propagacao, visualizacao e validacao ponta a ponta.
4. Padronizar tratamento de erro entre Google e HERE.
5. Revisar cache e politicas de TTL por tipo de uso:
   consulta individual vs visao geral.
6. Garantir que exportacao, logs e endpoints administrativos estejam consistentes com o contrato final.

### Entregavel

Backend unico, sem logica funcional critica espalhada em mais de um lugar.

### Criterio de saida

Uma mesma consulta deve produzir resultado previsivel, rastreavel e exportavel.

## Fase 4 - Integracao do Frontend

### Objetivo

Conectar o frontend novo ao backend consolidado sem acoplamento fragil.

### Acoes

1. Mapear o frontend Vite/React para consumir apenas o contrato oficial.
2. Substituir mocks por chamadas reais, mantendo um modo de desenvolvimento controlado.
3. Garantir renderizacao correta de:
   rota, incidentes, cores por trecho, marcadores de origem/destino e waypoints.
4. Estruturar estados de UI:
   carregando, sucesso, erro parcial, erro total e cache hit.
5. Revisar exportacao e favoritos a partir da API real.
6. Validar responsividade e clareza visual para uso operacional.

### Entregavel

Frontend conectado ao backend real e funcional para o fluxo principal.

### Criterio de saida

O usuario consegue consultar, interpretar e exportar uma rota sem depender de adaptacoes manuais.

## Fase 5 - Qualidade, Observabilidade e Seguranca Operacional

### Objetivo

Reduzir risco de regressao e melhorar previsibilidade.

### Acoes

1. Criar testes minimos para:
   classificacao de status, merge de fontes, parsing de waypoints e geracao de payload.
2. Adicionar testes de integracao para endpoints criticos.
3. Definir logs obrigatorios por consulta:
   tempo total, fonte com falha, metodo de busca e uso de cache.
4. Revisar limites de rate limit e comportamento de fallback.
5. Definir politicas basicas de operacao:
   timeout, retries, limpeza de cache e resposta a indisponibilidade parcial.

### Entregavel

Checklist tecnico de operacao e um conjunto minimo de testes automatizados.

### Criterio de saida

Falhas relevantes passam a ser detectaveis e diagnosticaveis sem analise manual extensa.

## Fase 6 - Validacao de Campo e Go-Live Controlado

### Objetivo

Colocar a solucao em uso com risco controlado.

### Acoes

1. Selecionar um conjunto curto de rotas reais criticas para homologacao.
2. Validar:
   geometria, waypoints, incidentes relevantes, tempos e exportacoes.
3. Comparar resultado do sistema novo com o comportamento esperado do processo atual.
4. Corrigir desvios antes de ampliar o uso.
5. Publicar a primeira versao com escopo reduzido e monitoramento ativo.

### Entregavel

Relatorio de homologacao com rotas testadas, falhas encontradas e decisoes de liberacao.

### Criterio de saida

O sistema entra em operacao porque foi validado em cenarios reais, nao apenas porque funcionou localmente.

## Priorizacao Recomendada

### P0 - Obrigatorio

- Definir backend canonico
- Fechar escopo da primeira entrega
- Formalizar contrato de API
- Garantir rota com waypoints obrigatorios ponta a ponta

### P1 - Necessario para consolidacao

- Integrar frontend real ao backend
- Padronizar exportacao, favoritos e estados de erro
- Criar testes de regressao basicos

### P2 - Evolucao

- Otimizar performance
- Refinar experiencia visual
- Expandir monitoramento e automacoes complementares

## Riscos que o Plano Precisa Controlar

1. Duplicidade de regra entre legado e backend novo.
2. Frontend acoplado a mocks ou campos instaveis.
3. Regressao em rotas com `via`.
4. Consumo excessivo de API por falta de cache adequado.
5. Validacao insuficiente em rotas criticas de negocio.

## Definicao de Sucesso

O plano sera bem executado quando:

1. existir uma unica base funcional para backend e uma unica para frontend,
2. o contrato de dados estiver estavel,
3. as rotas criticas com waypoints forem reproduzidas corretamente,
4. o fluxo principal (consultar, visualizar, exportar) funcionar de ponta a ponta,
5. e a equipe conseguir operar e evoluir o sistema sem depender de conhecimento disperso.

## Proximo Passo Recomendado

Executar imediatamente a Fase 0 e registrar a decisao arquitetural antes de qualquer nova implementacao. Sem esse corte, o projeto continua acumulando codigo, mas nao ganha direcao.
