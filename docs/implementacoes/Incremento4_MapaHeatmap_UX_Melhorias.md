# Incremento 4 — Mapa Heatmap, Correções de Crash e UX

**Data:** 03/03/2026  
**Contexto:** Sessão de refactoring e feature parity do frontend React com o projeto legado (`projeto_zero_separado`).

---

## Objetivo Principal

Atingir paridade de funcionalidades entre o novo stack React/Leaflet (`/consulta`, `/painel`) e o sistema legado em HTML puro (`projeto_zero_separado`), corrigindo crashes críticos e adicionando melhorias de UX.

---

## ✅ O que foi Feito (Acertos)

### 1. Motor de Segmentos de Trânsito (Traffic Heatmap)

**Arquivo:** `frontend/src/app/components/MapView.tsx`

- Implementado algoritmo de segmentação da rota por fator de congestionamento (`jam_factor`).
- Cada trecho da linha agora é dividido em `<Polyline>` individual com cor calculada pela proximidade ao ponto de fluxo mais próximo (distância euclidiana).
- Paleta de cores seguindo convenção HERE/Google:
  - 🟢 Verde: `jam < 3` → Normal
  - 🟡 Amarelo: `jam 3–5` → Leve  
  - 🟠 Laranja: `jam 6–7` → Moderado
  - 🔴 Vermelho: `jam >= 8` → Intenso/Parado
- Adicionado `<Tooltip sticky>` react-leaflet em cada segmento exibindo status e Jam Factor ao hover (comportamento Google Maps).

---

### 2. Correção do Crash `Invalid LatLng: (undefined, undefined)`

**Arquivo:** `frontend/src/app/components/MapView.tsx`

**Erro encontrado:**  
Ao clicar em "Visão Geral" de qualquer card, a tela exibia um erro fatal rosa do React (`Invalid LatLng` no Leaflet). O crash era silencioso no backend.

**Causa raiz:**  
O backend Python retorna `route_pts` em dois formatos dependendo da origem dos dados:
- Consulta individual: `[{lat, lng}, ...]` (objetos tipados)
- Visão Geral / GeoJSON: `[[lat, lng], ...]` (arrays)

O componente `MapView` tentava `p.lat` em todos os casos — se `p` era um Array, `p.lat` retornava `undefined`, e o Leaflet lançava a exceção.

**Solução aplicada:**
```tsx
const latlngs = routePts.map((p: any) => {
    if (Array.isArray(p)) return [p[0], p[1]] as [number, number];
    return [p.lat, p.lng] as [number, number];
}).filter(ll => ll[0] !== undefined && ll[1] !== undefined);
```

**Resultado:** Nenhum crash. O Leaflet recebe pontos válidos em ambos os formatos.

---

### 3. Correção do Bug de Filtro no Painel (`filteredRoads` stale)

**Arquivo:** `frontend/src/app/pages/PainelPage.tsx`

**Erro encontrado:**  
Ao abrir o Painel, todos os gauges marcavam zero e "Nenhum registro encontrado". Os cartões só apareciam depois de mexer em algum filtro.

**Causa raiz:**  
`filteredRoads` era calculado via `useMemo`, mas `roads` estava ausente da lista de dependências:
```tsx
// ❌ ANTES — Nunca recalculava quando roads carregava
}, [statusFilter, viaFilter, nomeFilter, ...]);

// ✅ DEPOIS — Recalcula quando a API retorna os dados
}, [roads, statusFilter, viaFilter, nomeFilter, ...]);
```

**Resultado:** Cards aparecem imediatamente ao carregar a página sem precisar interagir com filtros.

---

### 4. Renderização de Waypoints (`via_coords`) na Visão Geral

**Arquivo:** `frontend/src/app/components/MapView.tsx`

- Adicionado suporte à prop `viaCoords?: {lat, lng}[]`.
- Pinos numerados (1, 2, 3...) renderizados como `<Marker>` cinzas intermediários no trajeto.
- Replicando o comportamento dos "pontos de parada" do projeto legado.

---

### 5. Exibição de Coordenadas + Endereço na Consulta

**Arquivo:** `frontend/src/app/pages/ConsultaPage.tsx`

- Adicionados campos `origem` e `destino` (string `"lat,lng"`) à interface `ConsultaData`.
- Novo bloco visual "Rota" no sidebar abaixo do Status:
  - 🟢 `-23.333027,-46.823893` (em fonte monospace)
  - abaixo: `São Paulo (Cajamar)` (em cinza)
  - 🔴 `-8.295446,-35.057952`
  - abaixo: `Bahia (Lauro de Freitas)`

---

### 6. Correção do Fuso Horário (UTC → Brasília)

**Arquivo:** `frontend/src/app/pages/ConsultaPage.tsx`

**Erro encontrado:**  
"Consultado em: 2026-03-04 00:27:51" — exibindo UTC quando o usuário está em Brasília (UTC-3).

**Solução:**
```tsx
function toLocalBRT(utcStr?: string): string {
    const dt = new Date(utcStr.trim().replace(' ', 'T') + 'Z');
    return dt.toLocaleString('pt-BR', {
        timeZone: 'America/Sao_Paulo',
        ...
    });
}
```

**Resultado:** `"Consultado em: 03/03/2026, 21:27:51 (Brasília)"`.

---

### 7. Tooltips de Informação nos Cards de Métricas (ⓘ)

**Arquivo:** `frontend/src/app/pages/ConsultaPage.tsx`

- Adicionado prop `tooltip?: string` ao componente `KpiCard`.
- Renderizado um ícone `ⓘ` cinza ao lado do label de cada métrica.
- Ao hover, exibe popup darkmode com descrição técnica da métrica.
- Todos os 8 cards documentados com textos descritivos em PT-BR.

---

## ❌ Erros Encontrados (e Corrigidos)

| # | Erro | Arquivo | Causa | Correção |
|---|------|---------|-------|----------|
| 1 | `Invalid LatLng (undefined, undefined)` | `MapView.tsx` | Backend envia `[[lat,lng]]` mas frontend lia `p.lat` | Parser dinâmico com `Array.isArray(p)` |
| 2 | `Cannot read properties of undefined (reading '0')` | `MapView.tsx` | `latlngs` vazio acessado antes do guard | Early return antes de `buildSegments` |
| 3 | Cards não aparecem sem mexer no filtro | `PainelPage.tsx` | `roads` ausente nas deps do `useMemo` | Adicionado `roads` ao array de dependências |
| 4 | Timestamp UTC exibido sem conversão | `ConsultaPage.tsx` | `consultado_em` usado diretamente sem conversão | `toLocalBRT()` com `America/Sao_Paulo` |
| 5 | `getNearestJam` undefined no refactor | `MapView.tsx` | Variável renomeada para `getNearestFlow` mas ref antiga não atualizada | Corrigido a variável de inicialização `currentJam` |

---

## ⚠️ Pontos de Atenção (Débitos Técnicos)

1. **Backend não retorna `origem`/`destino` String no `/painel`** — Na visão agregada do Painel, o campo de coordenadas brutas pode não estar presente. A `ConsultaPage` recebe dados ao chamar `/rotas/RXX/consultar`, que já inclui esses campos.

2. **Sem testes automatizados para `MapView`** — O componente é crítico mas não tem testes. Um crash regrediria silenciosamente.

3. **`coletor.py` ainda precisa ser executado manualmente** — O GitHub Actions está configurado, mas o workflow não foi validado end-to-end em CI real.

4. **Tooltip nos segmentos só aparece quando há `flow_pts`** — Rotas sem dado de fluxo do HERE/Google ficam com um segmento único colorido pelo status geral, sem detalhes no tooltip.

---

## 📋 Próximos Passos

### Curto Prazo (próxima sessão)

- [ ] **Validar o GitHub Actions** — Testar o workflow `monitor_dinamico.yml` em repositório real para confirmar que o `coletor.py` executa com sucesso e os dados aparecem no Supabase.
- [ ] **Exibir dados do `/painel` nos cards com mais detalhe** — Incluir distância pré-definida e último horário de coleta nos `RouteCard`.
- [ ] **Adicionar legendas de cor no mapa** — Um pequeno widget fixo mostrando 🟢 Normal / 🟡 Leve / 🟠 Moderado / 🔴 Intenso, similar ao Google Maps.

### Médio Prazo

- [ ] **Fallback de Rota Aproximada** — Quando HERE não retorna geometria, desenhar linha tracejada origem→destino como o legado faz (já implementado no `app.js` legado, linha `~823`).
- [ ] **Exportação no `/consulta`** — Botões Excel/CSV individuais por rota como no sistema legado.
- [ ] **Testes automatizados** — Cobertura mínima para `MapView`, `PainelPage`, e endpoints `/painel` e `/rotas/RXX/consultar`.
- [ ] **"Explodir Rotas"** — Feature do legado que plotava múltiplas rotas simultaneamente no mapa com cores diferentes. Estrutura já está no `app.js` legado.

### Longo Prazo

- [ ] **Migração de autenticação** para Supabase Auth (eliminar `auth_local.py` temporário).
- [ ] **Mobile responsiveness** — O Painel e a página de Consulta não são totalmente responsivos.

---

## 🗂️ Arquivos Modificados Nesta Sessão

| Arquivo | Mudanças |
|---------|----------|
| `frontend/src/app/components/MapView.tsx` | Heatmap, Tooltip de segmento, parser Array/Object, `viaCoords` waypoints |
| `frontend/src/app/pages/ConsultaPage.tsx` | coords Origem/Destino, `toLocalBRT()`, `KpiCard` tooltips, `via_coords` prop |
| `frontend/src/app/pages/PainelPage.tsx` | Fix dep `roads` no `useMemo` do filtro |
| `backend/web/app.py` | Startup event para inicializar Supabase/config ao subir via `uvicorn` direto |
