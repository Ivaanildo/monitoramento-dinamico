# Incremento 2 — Consulta Individual com Mapa Leaflet

**Data:** 2026-03-03  
**Fase:** Finalização do Frontend (Consulta Page + Mapa)

---

## O que foi implementado

### 1. `ConsultaPage.tsx` — Reescrita Completa

O placeholder foi substituído por uma página completa de split layout:

**Layout:**
```
┌──────────────────────────────────────────────────────────┐
│ ← Painel  |  🔍  R01 · Hub A → Hub B        [Atualizar] │
├──────────────┬───────────────────────────────────────────┤
│ SIDEBAR 340px│         MAPA LEAFLET OSM (flex-1)         │
│ Status Pill  │  Polilinha verde/laranja/vermelha          │
│ 8 KPIs grid  │  Marcadores de Origem e Destino            │
│ Incidentes   │  Marcadores de Incidentes HERE             │
│ Waze / GMaps │                                            │
│ Fontes       │                                            │
└──────────────┴───────────────────────────────────────────┘
```

**Estados gerenciados:**
- `loading=true` → Spinner animado com contador de segundos + skeletons
- `loading=false, data` → Dados com animação de entrada (Framer Motion)
- `error` → Card vermelho com botão Retry

**KPIs exibidos na sidebar:**
- Status (pill colorido + incidente principal)
- Atraso (+X min ou "Sem atraso")
- Distância (km)
- Duração Normal vs. c/ Trânsito (min)
- Velocidade Atual / Livre (km/h)
- % Congestionado
- Jam Factor Avg / Max (HERE)
- Confiança (% + label)

**Links de navegação:**
- Botão Waze (abre em nova aba)
- Botão Google Maps (abre em nova aba)
- Botão ← Painel (retorna ao dashboard)
- Botão Atualizar (refaz a chamada real-time)

---

### 2. `MapView.tsx` — Novo Componente

Componente React-Leaflet com OSM tiles, lazy-loaded:

| Elemento | Detalhe |
|---|---|
| `<MapContainer>` | Centraliza automaticamente nos bounds da polilinha via `BoundsFitter` |
| `<TileLayer>` | OpenStreetMap tiles |
| `<Polyline>` | Colorida por status: 🟢 Normal / 🟠 Moderado / 🔴 Intenso |
| Marcador Origem | Ícone SVG verde com "O" |
| Marcador Destino | Ícone SVG vermelho com "D" |
| Marcadores Incidente | Ícone colorido por severidade + Popup com descrição |

---

### 3. Arquivos Modificados

| Arquivo | Mudança |
|---|---|
| `api.ts` | `getConsulta(rota_id)` adicionado; `credentials` corrigido para `"include"` |
| `main.tsx` | `import "leaflet/dist/leaflet.css"` adicionado |
| `package.json` | `react` e `react-dom` movidos de `peerDependencies` para `dependencies` |
| `RouteCard.tsx` | `id: number` → `id: string`; `onVerObs(id: number)` → `onVerObs(id: string)` |
| `inspect_excel.py` | `rota_id: i+1` (int) → `rota_id: f"R{i+1:02d}"` (string) |

---

## Bugs Encontrados e Corrigidos

> [!CAUTION]
> Os três bugs abaixo foram encontrados e corrigidos durante a sessão de implementação.

### Bug 1 — `react` / `react-dom` não instalados pelo npm

**Sintoma:** Vite iniciava mas errava com `Cannot find module 'react'`.

**Causa:** `react` e `react-dom` estavam em `peerDependencies` com `optional: true`. O npm não instala `peerDependencies` opcionais por padrão.

**Solução:** Movidos para `dependencies` em `package.json`. Reinstalação com `npm install --legacy-peer-deps` (necessário pois `react-leaflet@5` requer React 19, mas o projeto usa React 18).

**Arquivo:** `package.json`

---

### Bug 2 — `rota_id` gerado como inteiro no mock

**Sintoma:** Ao clicar em "visão geral" no card, a URL gerada era `/consulta?rota_id=4` (inteiro) em vez de `/consulta?rota_id=R04`.

**Causa:** `inspect_excel.py` linha 49 usava `"rota_id": i + 1` (Python int).

**Solução:**
```diff
-        "rota_id": i + 1,
+        "rota_id": f"R{i+1:02d}",
```

Arquivo regenerado: `mock_painel.json` (28 rotas com IDs `"R01"` a `"R28"`).

**Arquivo:** `inspect_excel.py` + `mock_painel.json`

---

### Bug 3 — Tipo `id` errado em `RouteCardProps`

**Sintoma:** TypeScript lint error + potencial runtime mismatch ao passar `rota_id` string para campo tipado como `number`.

**Causa:** `RouteCardProps.id` e `onVerObs` foram declarados com tipo `number` mas recebem string `"R01"`.

**Solução:**
```diff
- id: number;
+ id: string;
- onVerObs?: (id: number) => void;
+ onVerObs?: (id: string) => void;
```

**Arquivo:** `RouteCard.tsx`

---

## Fluxo de Navegação Final

```
/painel
  └─ [clica "visão geral" em card R04]
       └─ navigate("/consulta?rota_id=R04")
            └─ ConsultaPage: useSearchParams → "R04"
                 └─ api.getConsulta("R04") → GET /rotas/R04/consultar
                      └─ Backend: consulta HERE + Google em tempo real (~5-15s)
                           └─ Mapa + KPIs renderizados
```

## Próximo Passo

- Incremento 3: Histórico analítico (leituras do Supabase) e realtime no painel.
