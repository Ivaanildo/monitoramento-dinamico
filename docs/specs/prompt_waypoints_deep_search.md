# Prompt Base - Deep Search de Waypoints

Use este prompt para rodar varias pesquisas profundas (uma por trilha ou combinadas).

## Prompt
```text
Voce e um especialista senior em geospatial routing, traffic intelligence e otimização de custo em APIs (Google Routes + HERE Routing).

Contexto do projeto:
- Sistema: monitoramento dinamico de rotas corporativas no Brasil.
- Arquivo de rotas: backend/data/rotas.json
- Waypoints atuais no formato HERE: lat,lng!passThrough=true
- Orquestracao: backend/core/consultor.py
- HERE routing + corridor: backend/core/here_incidents.py
- Google routes traffic: backend/core/google_traffic.py
- Objetivo: aumentar precisao da rota e relevancia de incidentes sem estourar API/quota/custo.

Quero uma analise profunda com base em documentacao oficial e praticas de engenharia aplicavel.

Escopo da rodada:
[COLE AQUI UMA TRILHA, ex: "waypoints adaptativos por geometria e risco operacional"]

Responda obrigatoriamente neste formato:
1) Resumo executivo (max 10 linhas)
2) Achados tecnicos (bullet list)
3) Propostas de melhoria priorizadas (P0, P1, P2), cada uma com:
   - Problema atual
   - Solucao proposta
   - Mudancas concretas em codigo/config (com paths)
   - Impacto esperado (precisao, latencia, custo)
   - Risco e mitigacao
4) Plano de experimento A/B ou canary:
   - Metricas
   - Janela de medicao
   - Criterio de sucesso/falha
5) Guardrails de quota/custo:
   - Rate limiting
   - Retry/backoff
   - Cache e deduplicacao
6) Tabela de limites e observacoes por provider (Google/HERE)
7) Referencias oficiais com links e data de consulta

Regras:
- Nao inventar limite numerico sem citar fonte oficial.
- Se houver conflito entre fontes, destacar explicitamente.
- Priorizar recomendacoes que possam ser implementadas em backend Python atual.
- Sempre incluir uma versao "quick win em 1 dia" e outra "robusta em 2-4 semanas".
```

## Variantes de busca (copiar e colar em `Escopo da rodada`)
1. `limites atuais de waypoints + implicacoes de custo por SKU + estrategia de controle de quota`
2. `algoritmo de waypoint adaptativo por curvatura/heading/troca de rodovia`
3. `detecao de drift entre HERE e Google e recalibracao automatica de via`
4. `estrategia de segmentacao de rotas longas para reduzir erro e latencia`
5. `score de qualidade de waypoint e poda automatica de pontos redundantes`
6. `pipeline de reseed periodico de waypoints com validacao por KPI`
7. `observabilidade de rota: metricas, dashboards e alertas para 429/custo`

## Prompt Curto (quando precisar de varias rodadas rapidas)
```text
Analise o escopo abaixo para um sistema de monitoramento de rotas com waypoints (Google Routes + HERE Routing), proponha melhorias praticas priorizadas (P0/P1/P2), inclua impactos em precisao/latencia/custo, riscos, plano de experimento, guardrails de quota e referencias oficiais.

Escopo: [COLE AQUI]
Contexto tecnico: backend/data/rotas.json, backend/core/consultor.py, backend/core/google_traffic.py, backend/core/here_incidents.py
```
