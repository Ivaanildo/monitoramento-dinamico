# Contexto Atual - Incremento 1

**Data:** 2026-03-03
**Fase:** Finalização do Backend (Ordens 1 a 4)

## O que foi concluído com sucesso

O backend do "Projeto Zero" foi completamente adaptado para servir como API canônica para o novo painel agregado, garantindo isolamento entre o legado e a nova arquitetura de rotas.

As seguintes entregas foram realizadas e validadas através de 43 testes unitários e de integração:

### 1. Configuração e Autenticação
- Ajustado o `config.yaml` para mapear de forma segura o `rota_logistica.json`.
- Adicionado suporte a `auth_local` com login e validação de sessão em cookies HTTP-Only.
- Criados endpoints `POST /auth/login`, `POST /auth/logout` e `GET /auth/session`.

### 2. Leitura de Rotas Corporativas
- Modificada a engine base para ler diretamente as 20 rotas corporativas e adaptar automaticamente a malha rodoviária legacy (`rodovia_logica` e `via`) para a API de monitoramento ativa.
- Exposto o `GET /rotas` para servir exclusivamente estas 20 rotas em contrato estável.

### 3. Agregação e Painel
- Construído o `painel_service.py` que consulta as 20 rotas paralelamente, resolvendo a disponibilidade e consolidando os resultados no contrato `PainelRotasResponse`.
- Exposto o `GET /painel`, protegido nativamente por autenticação, suportando a exibição em tela cheia do dashboard integrado.

### 4. Exportação Otimizada
- Os endpoints CSV e Excel antigos foram adaptados e re-roteados para o novo fluxo.
- `GET /painel/exportar/excel` (e CSV) injetam dinamicamente o novo contrato aderente à visão gerencial.
- `GET /consultar/exportar/excel` atende necessidades analíticas da consulta individual usando o `ResultadoRotaDetalhado`.

### 5. Cobertura de Testes Unitários e TestClient (Camada 1 e 2)
- Módulos `tests/test_auth_local.py`, `tests/test_exportacoes.py`, `tests/test_painel_service.py` e ademais. O ciclo de QA com `pytest` está 100% verde (43 testes passados).

### 6. Banco de Dados (Ordem 5)
- **Integração com Supabase**: Adicionado driver de comunicação REST (`httpx`) para injetar os snapshots das rodovias consultadas nas tabelas `ciclos` e `snapshots_rotas`.
- **Degradação Elegante**: A comunicação com o Supabase falha de maneira controlada em caso de erros de conexão HTTP ou autenticação (ex: HTTP 401/500). Isso ocorre em Background sem quebrar o request principal do `/painel`, possuindo cobertura integral em `tests/test_persistencia_snapshot.py`.

### 7. Frontend Vite + React (Ordem 6)
- **Limpeza de Mocks Estruturais**: O React App substituiu os mocks locais por chamadas `fetch` à API Python operacionando no `http://127.0.0.1:8000` via proxy no Vite.
- **Roteamento Dinâmico**: Estruturado o `react-router` configurando as 3 páginas alvos: `/login`, `/painel` e a base da `/consulta`. O layout da página de Dashboard foi componentizado para limpar o `App.tsx`. Redirecionamento 401 implementado.

## Incremento 2 - Dashboard Dinâmico e UI Interativa (Em Andamento)

A base do Sistema (Incremento 1) está pronta e o projeto avançou para a camada visual dinâmica no frontend:

### 1. Injeção de Dados Reais do Excel
- Desenvolvido `inspect_excel.py` utilizando `openpyxl` (pandas bypassado). Este script extrai os atributos consolidados da planilha oficial `rodoviamonitor_pro` da empresa.
- **Mock Intercept:** O backend `painel_service.py` injeta silenciosamente o arquivo `mock_painel.json` extraído para preencher o Frontend com massa real em vez de tráfego local falso.

### 2. Conversão da Tabela para RouteCards Interativos
- O painel base (HTML table/linhas) foi inteiramente reescrito para um **Grid responsivo de CSS**.
- Foi implementado o componente `RouteCard.tsx` fiel à UI corporativa espelhada no Figma. Ele reflete as bordas com código de cores (Normal/Moderado/Intenso), além das "Pills" dos status.
- **Framer Motion Lado B:** O botão `ver obs.` reativa a malha e mostra os detalhes narrativos no verso do card com animações espelhadas sem destruir o DOM.

### 3. Ajustes Lógicos de Severidade e Filtros 
- Diferenciação visual entre vias válidas e vias passivas (**N/A** ou com falta de informações na rodovia), removendo seu peso dos medidores de status para não inflacionar falsos Normais.
- A aplicação Python agora força automaticamente o escalonamento para `Intenso` se uma via for considerada "Moderado" mas possuir delay superior a 30 minutos. 
- Componentes fixos dos Gauges (não desaparecem em buscas zeradas).

### Próximo Passo:
Início da construção do componente Mapa no `/consulta` contendo polígonos/linhas via React Leaflet consumindo a nova listagem do Painel.

---

## Incremento 2 - Consulta Individual com Mapa Leaflet (Concluído)

A página de Consulta Detalhada foi completamente implementada, fechando o ciclo de navegação Painel → Consulta.

### 1. ConsultaPage.tsx — Reescrita Completa

- **Layout split**: sidebar 340px (KPIs + incidentes + links) + canvas mapa `flex-1`.
- **Skeleton Loading**: contador de segundos animado enquanto a API real-time Google/HERE responde (~5-15s).
- **8 KPIs**: Atraso, Distância, Duração Normal/Trânsito, Velocidade Atual/Livre, % Congestionado, Jam Factor avg/max, Confiança.
- **Incidentes HERE**: lista com dot colorido por severidade (critical/major/minor).
- **Links externos**: Waze e Google Maps em nova aba.
- **Navegação**: botão ← Painel e botão Atualizar (força nova chamada real-time).

### 2. MapView.tsx — Novo Componente Leaflet

- OSM tiles via OpenStreetMap.
- Polilinha colorida por status: 🟢 Normal / 🟠 Moderado / 🔴 Intenso.
- Marcadores SVG inline de Origem (verde) e Destino (vermelho) com Popup.
- Marcadores de incidentes HERE com cor por severidade.
- Auto-fit de bounds ao polígono da rota (`BoundsFitter`).
- Lazy-loaded via `React.lazy` para não quebrar SSR.

### 3. Bugs Críticos Corrigidos

| Bug | Causa | Solução |
|---|---|---|
| `react` não instalado | `peerDependencies` opcionais ignoradas pelo npm | Movido para `dependencies` |
| `rota_id=4` na URL em vez de `R04` | `inspect_excel.py` gerava int `i+1` | Corrigido para `f"R{i+1:02d}"` |
| `id: number` no `RouteCard` | Tipo errado vs. string `"R01"` | Corrigido para `id: string` |

### Próximo Passo (Incremento 3):
Histórico analítico: tela de séries temporais por rota consumindo dados persistidos no Supabase. Realtime do painel via WebSocket ou polling curto.
