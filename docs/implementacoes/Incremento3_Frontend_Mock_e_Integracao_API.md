Documentação criada em docs/implementacoes/.

O arquivo cobre:

O que foi gerado: generate_mock_frontend.py, o mock_painel.json, e as mudanças no api.ts
Tabela de campos: quais vêm do Excel vs. quais ficam com 0 ou [] e precisam da API real
6 passos ordenados para remover o mock e conectar à API:
Configurar o proxy no vite.config.ts (sem CORS)
Restaurar o api.ts original com autenticação
Iniciar o backend FastAPI
Validar autenticação via cookie
Validar os campos ricos (mapa, velocidade, jam factor)
Deletar o mock_painel.json (limpeza final)
Diagrama do fluxo completo pós-integração# Incremento 3 — Frontend com Mock Excel + Roteiro de Integração à API Real

**Data:** 2026-03-03  
**Fase:** Frontend funcionando com dados reais do Excel (modo mock); Backend pronto para integração.

---

## O que foi implementado

### 1. Script de Geração de Mock: `generate_mock_frontend.py`

**Local:** `projeto_zero_separado/generate_mock_frontend.py`

Lê o relatório Excel oficial (`rodoviamonitor_pro_YYYYMMDD_HHMMSS.xlsx`) e gera o arquivo `mock_painel.json` na pasta `public/` do frontend.

**Lógica de mapeamento:**

| Campo Excel | Campo JSON (Frontend) | Observação |
|---|---|---|
| `Rodovia` | `sigla`, `nome` | `sigla` = parte antes da `/` |
| `Trecho` | `trecho` | Direto do Excel |
| `Status` | `status` | Capitalizado; força `Intenso` se Moderado + atraso > 30min |
| `Atraso (min)` | `atraso_min` | Inteiro, 0 se nulo |
| `Ocorrencia` | `ocorrencia`, `incidente_principal` | Texto direto |
| `Descricao / Observacoes` | `relato` | Texto direto |
| `Atualizado em` | `hora_atualizacao` | String datetime |
| `Confianca` | `confianca`, `confianca_pct` | Alta=95%, Média=75%, Baixa=50% |

**Campos derivados (sem correspondência direta no Excel):**

| Campo JSON | Valor Aplicado | Obs. |
|---|---|---|
| `hub_origem`, `hub_destino` | `"Origem N/A"` / `"Destino N/A"` | Substituir pela API real |
| `distancia_km` | `0.0` | Substituir pela API real |
| `velocidade_atual_kmh` | `0.0` | Substituir pela API real |
| `velocidade_livre_kmh` | `0.0` | Substituir pela API real |
| `jam_factor_avg`, `jam_factor_max` | `0.0` | Substituir pela API real (HERE) |
| `duracao_normal_min` | `60` (fixo) | Substituir pela API real |
| `duracao_transito_min` | `60 + atraso_min` | Substituir pela API real |
| `pct_congestionado` | `(atraso/60)*100` (estimativa) | Substituir pela API real |
| `route_pts` | `[]` (vazio) | Necessário para o mapa; preencher com lat/lng |
| `incidentes` | `[]` (vazio) | Necessário para os marcadores no mapa (HERE) |
| `fontes` | `["Excel Report"]` | Substituir com fontes reais |

**Como executar:**
```powershell
cd projeto_zero_separado
python generate_mock_frontend.py
```

O arquivo `mock_painel.json` é sobrescrito automaticamente em:
`Frontend/Criar frontend dinâmico/public/mock_painel.json`

---

### 2. Camada de API do Frontend: `api.ts`

**Local:** `Frontend/Criar frontend dinâmico/src/app/services/api.ts`

Atualmente em **modo mock**: ambas as funções (`get` e `getConsulta`) ignoram os endpoints reais e leem o arquivo estático `mock_painel.json`.

```typescript
// CONFIGURAÇÃO ATUAL (modo mock)
get: async (url: string) => {
    const res = await fetch("/mock_painel.json");
    return res.json();
}

getConsulta: async (rota_id: string) => {
    const res = await fetch("/mock_painel.json");
    const data = await res.json();
    const route = data.resultados.find((r: any) => r.rota_id === rota_id);
    return route;
}
```

---

## Estado Atual do Frontend

| Página | Funcionalidade | Fonte de Dados |
|---|---|---|
| `/painel` | ✅ Totalmente funcional | `mock_painel.json` (Excel) |
| `/consulta?rota_id=RXX` | ✅ Funcional com dados parciais | `mock_painel.json` (Excel) |
| Mapa (MapView) | ⚠️ Renderiza mas **sem traçado de rota** | `route_pts: []` vazio |
| Incidentes | ⚠️ Lista vazia | `incidentes: []` vazio |
| KPIs (vel., distância, jam) | ⚠️ Mostram `0` | Campos ausentes no Excel |

---

### Passo 3: Migração para o Backend (API Real) [Concluído]

1.  **Ajustes de Segurança e Payload (Frontend/Backend):**
    *   **Frontend `LoginPage.tsx`:** Alterado envio do corpo de autorização de `FormData` para um `json` puro (`application/json`) de maneira alinhada à interface do modelo Pydantic do FastAPI.
    *   **Autenticação com persistência local de sessão (`backend/app.py`)**: Corrigido bug de construção da resposta do `/auth/login`, onde a injeção do cabeçalho `Set-Cookie: projeto_zero_session` agora se atira na resposta final.

2.  **Restauração da Camada HTTP do Frontend (`api.ts`):**
    *   Arquivos restabelecidos com credenciais injetadas (`credentials: "include"`) utilizando os verdadeiros endpoints definidos no proxy Vite.

3.  **Deploy da Arquitetura de Polling Passiva (Dashboard Instantâneo via Supabase):**
    *   O motor outrora on-demand atrelado ao painel foi reescrito. As requisições à página `/painel` **não disparam requisições ativas ao Google Routes ou Here Traffic**.
    *   Ao iniciar GET em `/painel`, a API da aplicação faz uma consulta REST direta no PostgreSQL hospedado pelo `Supabase` lendo os snapshots passivos gerados rotineiramente na tabela de `ciclos`.

4.  **Worker via GitHub Actions:**
    *   Criado o `Monitoramento_Dinamico/backend/workers/coletor.py`, limitando a concorrência a 3 solicitações para economia de cotas, e acionado por meio do `monitor_dinamico.yml` a cada 30 minutos na infra de Actions.
---

## Próximos Passos — Integração com a API Real

Para remover completamente os mocks e consumir dados reais, os seguintes passos devem ser executados **na ordem indicada**:

---

### Passo 1 — Configurar o Proxy Vite (Sem CORS)

**Arquivo:** `Frontend/Criar frontend dinâmico/vite.config.ts`

Adicionar o bloco `server.proxy` para redirecionar as chamadas do frontend ao backend Python:

```typescript
// vite.config.ts
export default {
  server: {
    proxy: {
      "/painel": "http://127.0.0.1:8000",
      "/rotas": "http://127.0.0.1:8000",
      "/auth": "http://127.0.0.1:8000",
    },
  },
};
```

> [!NOTE]
> O back-end já expõe os endpoints `/painel` e `/rotas/{rota_id}/consultar` conforme documentado no Incremento 1. O proxy evita erros de CORS durante desenvolvimento local.

---

### Passo 2 — Restaurar `api.ts` para Chamar os Endpoints Reais

**Arquivo:** `src/app/services/api.ts`

Substituir o mock pela implementação autenticada original:

```typescript
export const api = {
  get: async (url: string) => {
    const res = await fetch(url, { credentials: "include" });
    if (!res.ok) {
      if (res.status === 401) throw new Error("Unauthorized");
      throw new Error("HTTP " + res.status);
    }
    return res.json();
  },

  getConsulta: async (rota_id: string) => {
    const res = await fetch(`/rotas/${rota_id}/consultar`, { credentials: "include" });
    if (!res.ok) {
      if (res.status === 401) throw new Error("Unauthorized");
      throw new Error("HTTP " + res.status);
    }
    return res.json();
  },
};
```

---

### Passo 3 — Iniciar o Backend Python

O backend (`projeto_zero_separado/`) deve estar rodando na porta `8000`:

```powershell
cd projeto_zero_separado
uvicorn main:app --reload --port 8000
```

> [!IMPORTANT]
> Confirmar que `config.yaml` está com as credenciais corretas (Google Maps API Key, HERE API Key, URL do Supabase).

---

### Passo 4 — Validar Autenticação

A `PainelPage` redireciona para `/login` ao receber erro `401`. Certificar que:

1. O cookie de sessão está sendo enviado corretamente (`credentials: "include"`).
2. O backend valida o cookie via `GET /auth/session`.
3. O login funciona via `POST /auth/login` com as credenciais armazenadas no `config.yaml`.

---

### Passo 5 — Validar Campos Ricos da ConsultaPage

Com a API real, os seguintes campos do `ConsultaData` serão populados automaticamente pelo backend (via HERE + Google Routes):

| Campo | Origem Real |
|---|---|
| `hub_origem`, `hub_destino` | `rota_logistica.json` (cadastro de rotas) |
| `distancia_km` | Google Routes API |
| `velocidade_atual_kmh`, `velocidade_livre_kmh` | HERE Traffic API |
| `pct_congestionado`, `jam_factor_avg`, `jam_factor_max` | HERE Traffic API |
| `duracao_normal_min`, `duracao_transito_min` | Google Routes API |
| `route_pts` | Google Routes API (array `lat/lng` da polilinha) |
| `incidentes` | HERE Incidents API (tipo, severidade, posição) |
| `link_waze`, `link_gmaps` | Gerado pelo backend a partir das coordenadas |

> [!TIP]
> Com `route_pts` populado, o mapa Leaflet renderizará a polilinha colorida da rota automaticamente. Com `incidentes` populado, os marcadores de acidentes e bloqueios aparecerão no mapa.

---

### Passo 6 — Remover o Mock (Limpeza Final)

Após validar a integração com a API real:

1. Deletar ou arquivar `Frontend/Criar frontend dinâmico/public/mock_painel.json`.
2. O script `generate_mock_frontend.py` pode ser mantido como ferramenta de fallback offline.

---

## Diagrama do Fluxo Final (Pós-Integração)

```
Navegador (React + Vite :5173)
    │
    ├─ GET /painel ──────────────► Backend FastAPI (:8000)
    │                                    │
    │                              painel_service.py
    │                              (paralelo: 20 rotas)
    │                                    │
    │                       ┌────────────┴────────────┐
    │                       ▼                         ▼
    │                  Google Routes             HERE Traffic
    │                  API (distância,           API (velocidade,
    │                  duração, polyline)        incidentes, jam)
    │                       │
    │                  Supabase (snapshot)
    │                       │
    │◄──────────── { resultados: [...20 rotas...] }
    │
    ├─ GET /rotas/R04/consultar ──► Backend FastAPI (:8000)
    │                                    │
    │                            consulta real-time (~5-15s)
    │◄──────────── ConsultaData completo com route_pts + incidentes
    │
    └─ MapView.tsx renderiza polilinha + marcadores
```

---

## Resumo dos Arquivos Relevantes

| Arquivo | Papel Atual |
|---|---|
| `projeto_zero_separado/generate_mock_frontend.py` | Converte Excel → `mock_painel.json` |
| `public/mock_painel.json` | Dados mock servidos pelo Vite |
| `src/app/services/api.ts` | **Modo mock ativo** — restaurar para API real no Passo 2 |
| `vite.config.ts` | Adicionar proxy no Passo 1 |
| `projeto_zero_separado/main.py` | Backend FastAPI — iniciar no Passo 3 |
| `projeto_zero_separado/config.yaml` | Confirmar credenciais das APIs externas |
