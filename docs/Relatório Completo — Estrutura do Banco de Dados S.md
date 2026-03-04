<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Relatório Completo — Estrutura do Banco de Dados Supabase `rodovia-monitor`

> **Projeto:** rodovia-monitor | **Organização:** ONG VALOR DE UMA VIDA
> **Region:** South America (sa-east-1) | **Tier:** Nano (FREE) | **Status:** Healthy
> **Data do relatório:** 03/03/2026

[^1]

***

## 1. Visão Geral dos Schemas

O banco possui **38 tabelas/views** distribuídas em 5 schemas:


| Schema | Função | Tabelas |
| :-- | :-- | :-- |
| `public` | Dados de negócio (sua aplicação) | 2 |
| `auth` | Autenticação nativa do Supabase | 14 |
| `realtime` | Engine de WebSockets/broadcast | 2 |
| `storage` | Gerenciamento de arquivos | 5+ |
| `extensions` | Views de métricas (pg_stat_statements) | 2 (views) |


***

## 2. Schema `public` — Tabelas de Negócio

### 2.1. Tabela: `ciclos`

**Finalidade:** Armazena os ciclos de monitoramento (agrupamentos temporais de snapshots de rotas).


| \# | Coluna | Tipo | Nullable | Default | Observação |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | `id` | `int4` (integer) | NOT NULL | `nextval(...)` | **PK**, auto-increment |
| 2 | `ts` | `text` | YES | — | Timestamp textual do ciclo |
| 3 | *(col 3)* | — | — | — | Verificar no schema |
| 4 | `fontes` | `text` | YES | — | Fontes de dados utilizadas |
| 5 | *(col 5)* | — | — | — | — |
| 6 | `ts_iso` | `text` | YES | — | Timestamp em formato ISO 8601 |

**Contagem de linhas:** ~10 registros
**Tamanho:** 48 kB total / 8 kB de dados

***

### 2.2. Tabela: `snapshots_rotas`

**Finalidade:** Registra cada snapshot de rota monitorada, vinculado a um ciclo. É a tabela principal de dados operacionais.


| \# | Coluna | Tipo | Nullable | Observação |
| :-- | :-- | :-- | :-- | :-- |
| 1 | `id` | `int4` (integer) | NOT NULL | **PK**, auto-increment |
| 2 | `ciclo_id` | `int4` (integer) | YES | **FK → ciclos(id)** |
| 3 | `trecho` | `text` | YES | Trecho da rodovia |
| 4 | `rodovia` | `text` | YES | Nome/código da rodovia (ex: BR-116) |
| 5 | `sentido` | `text` | YES | Sentido do tráfego |
| 6 | `status` | `text` | YES | Status atual do trecho |
| 7 | `ocorrencia` | `text` | YES | Ocorrência/incidente registrado |
| 8 | *(col 8)* | — | — | — |
| 9 | `confianca_pct` | `float8` (double precision) | YES | Percentual de confiança (0–100) |
| 10 | `conflito_fontes` | `int4` (integer) | YES | Indicador de conflito entre fontes |
| 11 | *(col 11)* | — | — | — |
| 12 | `ts_iso` | `text` | YES | Timestamp ISO 8601 do snapshot |

**Contagem de linhas:** ~200 registros
**Tamanho:** 112 kB total / 56 kB de dados / ~56 kB de índices

***

## 3. Relacionamentos (Foreign Keys)

```
snapshots_rotas.ciclo_id ──FK──► ciclos.id
  ON UPDATE: NO ACTION
  ON DELETE: NO ACTION
```

**Diagrama ER simplificado:**

```
ciclos (1) ──────────────── (N) snapshots_rotas
  id  ◄──── ciclo_id
```


***

## 4. Constraints

| Tabela | Constraint | Tipo | Coluna(s) |
| :-- | :-- | :-- | :-- |
| `ciclos` | `ciclos_pkey` | PRIMARY KEY | `id` |
| `snapshots_rotas` | `snapshots_rotas_pkey` | PRIMARY KEY | `id` |
| `snapshots_rotas` | `snapshots_rotas_ciclo_id_fkey` | FOREIGN KEY | `ciclo_id → ciclos.id` |


***

## 5. Índices

| Tabela | Índice | Tipo | Coluna | Único? |
| :-- | :-- | :-- | :-- | :-- |
| `ciclos` | `ciclos_pkey` | BTREE | `id` | ✅ Sim |
| `ciclos` | `idx_ciclos_ts_iso` | BTREE | `ts_iso` | ❌ Não |
| `snapshots_rotas` | `snapshots_rotas_pkey` | BTREE | `id` | ✅ Sim |

> **Observação:** O índice `idx_ciclos_ts_iso` foi criado explicitamente para otimizar queries por timestamp ISO — indica uso de filtragem/ordenação temporal frequente.

***

## 6. Row-Level Security (RLS)

Ambas as tabelas têm RLS **ativo** com **3 políticas cada**.

### Tabela `ciclos`

| Política | Comando | Roles | Descrição |
| :-- | :-- | :-- | :-- |
| `Backend full access ciclos` | `ALL` | `service_role` (?) | Acesso total para o backend |
| `Leitura publica ciclos` | `SELECT` | `authenticated` | Usuários autenticados podem ler |
| `anon_select_ciclos` | `SELECT` | `anon` | Usuários anônimos podem ler |

### Tabela `snapshots_rotas`

| Política | Comando | Roles | Descrição |
| :-- | :-- | :-- | :-- |
| `Backend full access snapshots` | `ALL` | `service_role` (?) | Acesso total para o backend |
| `Leitura publica snapshots` | `SELECT` | `authenticated` | Usuários autenticados podem ler |
| `anon_select_snapshots` | `SELECT` | `anon` | Usuários anônimos podem ler |

> **Padrão:** Leitura pública (inclusive anon) para ambas as tabelas. Escrita restrita ao backend via `service_role`.

***

## 7. Realtime (WebSockets)

| Publication | Tabelas incluídas | INSERT | UPDATE | DELETE |
| :-- | :-- | :-- | :-- | :-- |
| `supabase_realtime` | `snapshots_rotas` ✅ | ✅ | ✅ | ✅ |

> **Atenção:** Apenas `snapshots_rotas` está na publicação de realtime. A tabela `ciclos` **NÃO** está habilitada para Realtime — se precisar de eventos ao vivo em `ciclos`, é necessário adicioná-la à publication.

***

## 8. Triggers \& Funções Customizadas

| Item | Situação |
| :-- | :-- |
| Triggers no schema `public` | **Nenhum** |
| Funções customizadas no schema `public` | **Nenhuma** |


***

## 9. Schemas de Sistema (Supabase Built-in)

### Schema `auth` (14 tabelas)

Gerenciado internamente pelo Supabase:

- `users`, `identities`, `sessions`, `audit_log_entries`
- `mfa_factors`, `mfa_challenges`, `mfa_amr_claims`
- `flow_state`, `sso_providers`, `saml_providers`, `saml_relay_states`
- `oauth_clients`, `oauth_client_states`, `oauth_consents`
- `one_time_tokens`, `schema_migrations`, `instances`, `custom_oauth_providers`


### Schema `realtime` (2 tabelas)

- `messages`, `schema_migrations`


### Schema `storage` (5+ tabelas)

- `buckets`, `buckets_analytics`, `buckets_vectors`
- `migrations`, `s3_multipart_uploads`, `s3_multipart_uploads_parts`, `vector_indexes`

***

## 10. Resumo Executivo e Observações

### Arquitetura Atual

```
public.ciclos          ← Tabela mãe (10 registros)
  └─ public.snapshots_rotas  ← Tabela filha (200 registros, Realtime ativo)
```


### Pontos Fortes ✅

- Estrutura simples, clara e focada no domínio (monitoramento de rodovias)
- RLS bem configurado com separação anon/authenticated/backend
- Índice em `ts_iso` para performance em queries temporais
- Realtime habilitado em `snapshots_rotas` para dados ao vivo


### Pontos de Atenção ⚠️

1. **`ciclos` fora do Realtime** — se o frontend precisa reagir à criação de novos ciclos em tempo real, adicionar à publication
2. **FK sem CASCADE** — `ON DELETE NO ACTION` pode causar erros ao tentar deletar um ciclo com snapshots vinculados; considerar `ON DELETE CASCADE` ou `ON DELETE SET NULL`
3. **Coluna `ts` e `ts_iso` redundantes** — ambas em `ciclos` e `snapshots_rotas` armazenam timestamps em `text`; considerar migrar para `timestamptz` nativo para melhor performance e consistência
4. **Sem triggers de auditoria** — não há rastreio automático de `created_at`/`updated_at`; considerar adicionar
5. **Poucas linhas** — banco ainda em fase inicial/desenvolvimento; monitorar crescimento para planejar particionamento ou archiving de `snapshots_rotas`

<div align="center">⁂</div>

[^1]: https://supabase.com/dashboard/project/onaenotqyfxpvlofymzg/sql/8f068c1f-fa18-4c1d-8cc1-bbcd884167a8

