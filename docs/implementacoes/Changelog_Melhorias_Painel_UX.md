# Changelog — Melhorias do Painel e UX

Registro das alterações e melhorias implementadas no painel de monitoramento de vias.

---

## 1. StatusTicker (Ticker de Alertas)

### Velocidade da animação
- **Antes:** 25s por ciclo
- **Depois:** 60s por ciclo
- **Motivo:** Texto passava rápido demais, dificultando a leitura

### Background por contexto de tráfego
- Cada trecho de mensagem recebe fundo leve conforme o tipo:
  - **TRÁFEGO INTENSO** → vermelho suave (`rgba(239, 68, 68, 0.2)`)
  - **TRÁFEGO MODERADO** → laranja suave (`rgba(249, 115, 22, 0.2)`)
  - **FLUXO NORMAL** → verde suave (`rgba(34, 197, 94, 0.15)`)
- Separador "✦" entre trechos
- Padding e border-radius por segmento para melhor leitura

---

## 2. KPI Cards (Consulta Individual)

### Tooltip do KPI Confiança
- Adicionado tooltip informativo (ⓘ) ao card "Confiança"
- Texto: *"Nível de confiabilidade dos dados de trânsito agregados (Google + HERE). Alta = dados mais precisos; Baixa = possível variação nos resultados."*

### Reposicionamento dos tooltips
- **Problema:** Tooltips invadiam a área do mapa
- **Solução:** Alinhamento `right-0` em vez de centralizado, mantendo tooltips dentro da sidebar

---

## 3. Links de Navegação (Waze e Google Maps)

### Formato dinâmico A→B
- **Waze:** `https://www.waze.com/pt-BR/live-map/directions?from=X&to=Y&navigate=yes`
  - Coordenadas com prefixo `ll.`
  - Aceita endereços ou Place IDs
- **Google Maps:** `https://www.google.com/maps/dir/?api=1&origin=X&destination=Y`
  - Formato oficial Maps URLs API
  - Parâmetro `api=1` obrigatório

### Arquivos alterados
- `backend/core/consultor.py` — funções `_link_waze` e `_link_gmaps`
- Helper `_is_coord()` para detectar coordenadas `lat,lng`

---

## 4. Painel de Gauges (Expandível)

### Botão expandir/recolher
- Barra sempre visível com totais (Intenso, Moderado, Normal)
- Chevron como botão (sem texto "Expandir"/"Recolher")
- Animação suave ao expandir/recolher

### Ordem e distribuição visual
- **Ordem:** Intenso → Moderado → Normal (prioridade por severidade)
- **Distribuição na barra recolhida:**
  - Intenso: alinhado à esquerda
  - Moderado: centralizado
  - Normal: alinhado à direita
- Grid responsivo: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`

---

## 5. Indicador de Atualização (Version Check)

### Funcionalidade
- Verifica periodicamente se há nova versão do frontend
- **Nova versão:** ponto amarelo; clique recarrega a página
- **Falha na verificação:** ponto cinza; tooltip "Verificação indisponível"
- **Tudo ok:** nenhum indicador visível

### Implementação
- `public/version.json` gerado no build (plugin Vite)
- Hook `useVersionCheck` — fetch a cada 5 min e em `visibilitychange`
- Componente `VersionIndicator` envolvido em `ErrorBoundaryFallback` para evitar tela branca

---

## 6. Layout do Header

### Centralização
- **"Monitoramento de Vias":** centralizado no header (3 colunas: ícone | título | logo+relógio)
- **"Visão Geral das Rotas":** seção centralizada com título e contador

### Título responsivo
- `text-xl` (mobile) → `text-2xl` (sm) → `text-3xl` (md) → `text-4xl` (lg)
- `whitespace-nowrap` para evitar quebra de linha

---

## 7. Ordenação Hierárquica das Rotas

### Ordem padrão por severidade
- **1º** Intenso
- **2º** Moderado
- **3º** Normal
- **4º** Erro
- **5º** N/A / Sem dados

- Ocorrências mais severas aparecem primeiro na Visão Geral
- Ordenação manual (Status, Sigla, Nome etc.) continua prevalecendo quando aplicada

---

## 8. Alinhamento dos RouteCards

### Correção de layout
- Grid com `items-stretch` para mesma altura na linha
- Wrapper `motion.div` com `flex` e `min-h-0`
- `RouteCard` com `flex-1 w-full` para preencher a célula
- Cards alinhados em altura e largura na mesma linha

---

## Arquivos Modificados

| Arquivo | Alterações |
|---------|------------|
| `frontend/src/app/components/StatusTicker.tsx` | Velocidade, segmentos coloridos |
| `frontend/src/app/components/RouteCard.tsx` | flex-1, w-full |
| `frontend/src/app/components/VersionIndicator.tsx` | Novo componente |
| `frontend/src/app/components/ErrorBoundaryFallback.tsx` | Novo componente |
| `frontend/src/app/hooks/useVersionCheck.ts` | Novo hook |
| `frontend/src/app/pages/PainelPage.tsx` | Gauges, header, ordenação, VersionIndicator |
| `frontend/src/app/pages/ConsultaPage.tsx` | Tooltip Confiança, tooltips reposicionados |
| `frontend/vite.config.ts` | Plugin version, ErrorBoundary |
| `frontend/public/version.json` | Novo arquivo gerado no build |
| `backend/core/consultor.py` | Links Waze/Google dinâmicos |
| `backend/mock_api_server.py` | Links no mock (consistência) |

---

*Documento gerado em 04/03/2026*
