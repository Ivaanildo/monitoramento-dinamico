# Waypoints Turbo - Contexto e Trilhas de Melhoria

## Objetivo
Criar base tecnica para varias rodadas de deep search focadas em aumentar precisao de rota com waypoints, mantendo custo e quota de API sob controle.

## Contexto Atual no Projeto
- Fonte de rotas corporativas: `backend/data/rotas.json`
- Formato atual de waypoint HERE: `lat,lng!passThrough=true`
- Orquestracao de consulta: `backend/core/consultor.py`
- Roteamento + corridor HERE: `backend/core/here_incidents.py`
- Trafego Google Routes: `backend/core/google_traffic.py`
- Endpoint principal de consulta: `GET /consultar` em `backend/web/app.py`

## Estado Tecnico Relevante
- As rotas predefinidas ja usam `via` em `rotas.json`.
- O backend faz chunking para rotas longas no HERE.
- O backend envia `via` tambem para Google (`intermediates`) com limite configuravel.
- Existem controles de ritmo (throttle) para reduzir burst e evitar estouro de taxa.

## Variaveis de Controle (runtime)
- `GOOGLE_ROUTES_MAX_INTERMEDIATES`
- `GOOGLE_ROUTES_MIN_INTERVAL_MS`
- `HERE_ROUTING_MAX_VIA_PER_CHUNK`
- `HERE_MIN_INTERVAL_MS`

## Oportunidades de Turbo (para deep search)
1. Waypoints adaptativos por geometria:
- Definir densidade de waypoints por curvatura, mudanca de heading e troca de rodovia.
- Evitar distribuicao uniforme quando a rota cruza area urbana complexa.

2. Waypoints adaptativos por risco operacional:
- Aumentar densidade em trechos historicamente instaveis (congestionamento, incidentes, obras).
- Reduzir densidade em trechos estaveis para economizar chamadas.

3. Politica hibrida HERE + Google:
- Gerar waypoint base pelo HERE e validar desvio pelo Google.
- Detectar drift entre providers e recalibrar `via` automaticamente.

4. Segmentacao inteligente de rota:
- Segmentar por distancia + complexidade (nao so por quantidade de via).
- Definir chunk dinamico com base em limite de URL/payload e latencia alvo.

5. Qualidade de waypoint:
- Criar score por waypoint (relevancia, redundancia, contribuicao real para aderencia).
- Podar waypoints de baixo valor automaticamente.

6. Pipeline de refresh:
- Re-seedar waypoints em janela fixa (ex: semanal) e por gatilho (desvio acima de limiar).
- Versionar snapshots de via por rota e comparar regressao de precisao.

7. Guardrails de custo e quota:
- Rate-limit por provider, circuit-breaker, retry com backoff exponencial.
- Cache por assinatura de rota (origem, destino, via normalizada, horario).

## KPIs para comparar estrategias
- Erro medio de aderencia da rota (distancia da polilinha de referencia).
- Percentual de incidentes relevantes capturados no corredor.
- Tempo medio de resposta por consulta.
- Custo por consulta (estimado por SKU e volume).
- Taxa de erro 429/5xx por provider.

## Pacote de Deep Searches Recomendado
1. Limites atuais e comportamento de waypoints em Google Routes e HERE Routing.
2. Tecnicas de map matching e simplificacao de polilinha com preservacao de trajetoria.
3. Estrategias de sampling adaptativo para rotas longas.
4. Heuristicas para reduzir falsos positivos de incidentes fora da rodovia alvo.
5. Praticas de observabilidade para quota/custo em APIs de rota.

## Links de Documentacao Oficial (seed)
- Google Routes API overview:
  - https://developers.google.com/maps/documentation/routes
- Google Routes Waypoint reference:
  - https://developers.google.com/maps/documentation/routes/reference/rest/v2/Waypoint
- Google Routes usage and billing:
  - https://developers.google.com/maps/documentation/routes/usage-and-billing
- Google web service best practices:
  - https://developers.google.com/maps/documentation/route-optimization/web-service-best-practices
- HERE Routing API docs:
  - https://developer.here.com/documentation/routing-api/dev_guide/topics/routing-requests.html
- HERE pricing/plans:
  - https://www.here.com/get-started/pricing?cid=Freemium-1

## Entregavel esperado de cada deep search
- Hipotese clara
- Mudanca tecnica sugerida (codigo/config)
- Impacto esperado em precisao, latencia e custo
- Risco operacional
- Experimento minimo para validar
- Criterio de aceite objetivo
