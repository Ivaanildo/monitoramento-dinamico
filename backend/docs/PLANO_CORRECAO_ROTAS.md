# Plano de Correção — Rotas e Geometria Detalhada

**Versão:** 2.0
**Atualizado:** 2026-03-01
**Contexto:** Gerenciadora de risco — rotas obrigatórias para caminhoneiros. Desvio de rota = bloqueio do veículo.

---

## Status de Implementação

| Fase | Descrição | Status |
|------|-----------|--------|
| 1 | Waypoints (`via`) propagados até a API HERE | ✅ Concluído |
| 2 | Fatiamento automático para rotas >23 waypoints | ✅ Concluído |
| 3 | Coloração por segmento na polyline do mapa | ✅ Concluído |
| 4 | Pinos numerados nos waypoints intermediários | ✅ Concluído |

---

## 1. Problemas Originais

| # | Problema | Impacto | Prioridade |
|---|----------|---------|------------|
| 1 | **Visão Geral**: botão traça reta verde em vez da geometria real | Rota de bloqueio incorreta | **Crítica** |
| 2 | **Waypoints ignorados**: `via` do `favoritos.json` nunca usado | API calcula rota livre; pode desviar | **Crítica** |
| 3 | **Polyline toda vermelha**: trânsito intenso pinta toda a rota | Perda de informação: congestionamento localizado | **Média** |
| 4 | **Geometria indisponível**: fallback desenha reta | Inaceitável para gestão de risco | **Crítica** |

---

## 2. Arquitetura Após Correções

```
[Visão Geral] → GET /visao-geral
                    ↓
              _obter_resultados_visao_geral()
                    ↓
              _consultar_uma(r)
                ├── extrai via = r["here"]["via"]
                └── consultor.consultar(config, orig, dest, via)
                          ↓
                    here_incidents.consultar(orig, dest, via)
                          ↓
                    _obter_polyline_rota(lat1, lng1, lat2, lng2, via)
                    _call_routing_chunks(via)  ← fatiamento automático
                          ↓
                    GET router.hereapi.com/v8/routes
                      ?origin=...&destination=...&via=...&via=...
```

---

## 3. Fase 1 — Waypoints na API HERE

### Arquivos Modificados
- `core/here_incidents.py` — `_obter_polyline_rota` e `consultar` aceitam `via: list[str] | None`
- `core/consultor.py` — `consultar` aceita e repassa `via`
- `web/app.py` — `_consultar_uma` extrai e passa `via`; `_carregar_rotas_predefinidas` inclui `via`
- `web/app.py` — endpoint `/consultar` aceita `via` como query param

### Formato dos Waypoints HERE

```http
GET https://router.hereapi.com/v8/routes
  ?origin=-23.333027,-46.823893
  &destination=-8.295446,-35.057952
  &via=-22.880951,-46.403933!passThrough=true
  &via=-22.376394,-45.941018!passThrough=true
  &return=polyline
```

O formato `lat,lng!passThrough=true` está correto para a HERE Routing v8.
A biblioteca `requests` aceita `params["via"] = ["coord1", "coord2"]` e gera `via=coord1&via=coord2`.

---

## 4. Fase 2 — Fatiamento Automático (>23 waypoints)

### Problema
HERE Routing v8 suporta até ~25 waypoints por requisição. A R01 (SP→PE) tem 29 waypoints.

### Solução Implementada
`_call_routing_chunks` em `core/here_incidents.py`:

- Constante `_MAX_VIA_PER_CHUNK = 23`
- Divide `via` em fatias: `[orig → via[0..22] → via[22]]`, `[via[22] → via[23..28] → dest]`
- Faz requisições em paralelo (ThreadPoolExecutor)
- Concatena as polylines resultantes em ordem

### Eixo Logístico R01 (São Paulo → Suape/PE)

| Pino | Rodovia | Coordenadas |
|------|---------|-------------|
| Origem | SP (Guarulhos) | -23.333027, -46.823893 |
| 1–10 | SP-330 → BR-381 | ... |
| 11–20 | BR-381 → BR-116 | ... |
| 21–29 | BR-116 → BR-101 | ... |
| Destino | Suape/PE | -8.295446, -35.057952 |

---

## 5. Fase 3 — Coloração por Segmento

### Problema Anterior
`renderMapa()` usava `routeColor = STATUS_COLORS[status]` para toda a polyline.
Se `status === "Intenso"`, pintava **tudo** de vermelho.

### Solução Implementada (`web/static/index.html` — `renderMapa`)

Algoritmo dentro do bloco `geojson`, quando `flow_pts` existem:

1. Cria glow transparente (hitbox para tooltip em toda a rota)
2. Para cada par consecutivo de pontos da polyline, calcula o ponto médio
3. Encontra o `flow_pt` mais próximo (distância euclidiana em graus)
4. Agrupa segmentos consecutivos de mesma cor em uma única `L.polyline`
5. Fallback: se não houver `flow_pts`, mantém polyline monocor por status

```js
function _nearestJam(midLat, midLng) {
  let best = null, bestD = Infinity;
  for (const fp of fpData) {
    const d = (fp.lat - midLat) ** 2 + (fp.lng - midLng) ** 2;
    if (d < bestD) { bestD = d; best = fp; }
  }
  return best ? jamColor(best.jam) : routeColor;
}
```

### Escala de Cores (jamColor)

| Jam Factor | Cor | Significado |
|------------|-----|-------------|
| 0 | `#3498db` (azul) | Sem dados |
| 1–2 | `#27ae60` (verde) | Livre |
| 3–5 | `#f39c12` (amarelo) | Moderado |
| 6–7 | `#e67e22` (laranja) | Intenso |
| ≥ 8 | `#c0392b` (vermelho) | Parado |

---

## 6. Fase 4 — Pinos Numerados nos Waypoints

### Problema Anterior
Apenas origem (círculo verde) e destino (círculo vermelho) apareciam no mapa.
Os 29 waypoints `via` da R01 eram invisíveis.

### Solução Implementada

#### Backend (`web/app.py` — `_consultar_uma`)
Parsing dos waypoints após a consulta:
```python
via_raw = r.get("here", {}).get("via", [])
via_coords = []
for v in via_raw:
    try:
        coords_str = v.split("!")[0].split(",")
        via_coords.append({"lat": float(coords_str[0]), "lng": float(coords_str[1])})
    except Exception:
        pass
resultado["via_coords"] = via_coords
```

#### Frontend (`web/static/index.html`)

**CSS:**
```css
.via-pin {
  width: 22px; height: 22px;
  background: #1a1a1a; color: #fff;
  border-radius: 50%; border: 2px solid #fff;
  font-size: 10px; font-weight: bold;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.5);
}
```

**JS (em `renderMapa`, seção 5):**
```js
const viaCoords = data.via_coords || [];
if (viaCoords.length > 0) {
  const viaLayers = viaCoords.map((pt, idx) =>
    L.marker([pt.lat, pt.lng], {
      icon: L.divIcon({
        className: '',
        html: `<div class="via-pin">${idx + 1}</div>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11],
      }),
      interactive: false,
    })
  );
  _mVia = L.featureGroup(viaLayers).addTo(map);
}
```

**Estado:** `let _mVia = null;` — limpo no início de `renderMapa` e em `limparMapa`.

---

## 7. Arquivos Modificados (Resumo)

| Arquivo | Fases | Mudanças |
|---------|-------|---------|
| `core/here_incidents.py` | 1, 2 | `via` em `_obter_polyline_rota` e `consultar`; fatiamento `_call_routing_chunks` |
| `core/consultor.py` | 1 | `via` em `consultar` |
| `web/app.py` | 1, 4 | `via` em `_consultar_uma`; `via_coords` em resultado; `via` em `/consultar` |
| `web/static/index.html` | 3, 4 | Polyline segmentada por jam; pinos numerados; CSS `.via-pin`; `_mVia` |

---

## 8. Checklist de Validação

### Visão Geral — R01 (SP → PE)
- [ ] Mapa exibe rota **sinuosa** seguindo SP-330 → BR-381 → BR-116 → BR-101
- [ ] Polyline com **cores variando por trecho** (verde/amarelo/laranja/vermelho por jam)
- [ ] **29 pinos numerados** (1–29) nos waypoints intermediários
- [ ] Origem verde e destino vermelho mantidos
- [ ] Tooltip ao passar o mouse exibe status, velocidade e atraso

### Compatibilidade
- [ ] Consulta manual (sem `via`) continua funcionando sem pinos
- [ ] Rotas sem `flow_pts` exibem polyline monocor (fallback)
- [ ] Export Excel/CSV da Visão Geral mantém dados corretos
- [ ] Cache funciona normalmente (TTL 300s)

---

## 9. Limites e Rate Limits

| API | Limite | Mitigação |
|-----|--------|-----------|
| HERE Routing v8 | ~25 waypoints por request | `_MAX_VIA_PER_CHUNK = 23` |
| HERE Traffic | 5.000 transações/mês | Cache TTL 300s |
| Google Routes | 40.000/mês (free tier) | Cache; evitar redundâncias |

**Atenção:** Visão Geral com 20 rotas = 20 consultas paralelas a cada 5 min.
288 ciclos/dia ≈ 5.760 consultas/dia — pode exceder limite HERE.
Considere aumentar TTL para 15–30 min na Visão Geral se necessário.

---

## 10. Glossário

| Termo | Significado |
|-------|-------------|
| **Waypoint** | Ponto de passagem obrigatório na rota |
| **PassThrough** | Waypoint que a rota deve passar sem parar |
| **Polyline** | Sequência de coordenadas formando a linha da rota no mapa |
| **Corridor** | Faixa ao redor da polyline usada para buscar incidentes |
| **Jam Factor** | Métrica HERE: 0 = livre, 10 = parado |
| **flow_pts** | Pontos retornados pelo HERE Flow com `{ lat, lng, jam }` por segmento |
| **via_coords** | Lista de `{ lat, lng }` extraída dos waypoints `via` para renderização |

---

## 11. Referências

- [HERE Routing API v8 — Via / PassThrough](https://www.here.com/docs/bundle/routing-api-developer-guide-v8/page/tutorials/via.html)
- [HERE Routing API v8 — Calculate Route](https://www.here.com/docs/bundle/routing-api-developer-guide-v8/page/tutorials/calculate-route.html)
- [Google Routes API v2 — Waypoints](https://developers.google.com/maps/documentation/routes/waypoints)
- Eixo logístico SP → Suape: SP-330 › SP-021 › BR-381 › BR-116 › BR-324 › BR-101
