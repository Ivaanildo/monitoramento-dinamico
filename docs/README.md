# Documentacao

Esta pasta concentra a documentacao tecnica e operacional do projeto. A ideia aqui e simples: o `README.md` da raiz responde "o que e e como subir", enquanto `docs/` responde "como isso funciona e como operar".

## Comece por aqui

| Documento | Quando usar |
| --- | --- |
| [`getting-started.md`](getting-started.md) | primeiro setup local, dependencias, env vars e verificacao |
| [`api-e-operacao.md`](api-e-operacao.md) | endpoints, auth, exportacao, worker e observabilidade |
| [`arquitetura/README.md`](arquitetura/README.md) | visao estrutural do sistema e diagramas Mermaid |

## Mapa da pasta

### Base tecnica

- [`arquitetura/`](arquitetura/README.md): visao geral, fluxo de dados, deploy e estrutura do codebase.
- [`migration_add_rota_id_field.sql`](migration_add_rota_id_field.sql): ajuste de schema relacionado a rotas.
- [`migration_add_ocorrencia_fields.sql`](migration_add_ocorrencia_fields.sql): ajuste de schema para ocorrencias.

### Contexto e decisao

- [`Fase0_Decisao_Arquitetural.md`](Fase0_Decisao_Arquitetural.md)
- [`Fase0_Questionario_Fechado.md`](Fase0_Questionario_Fechado.md)
- [`Oneshoot_v2.md`](Oneshoot_v2.md)

### Historico de implementacao

- [`implementacoes/`](implementacoes/): planos de incremento, changelogs e notas de deploy.

### Material de pesquisa e apoio

- [`notebooklm/00-INDEX.md`](notebooklm/00-INDEX.md): base narrativa extensa sobre produto, stack e operacao.
- [`reports/`](reports/): seguranca, ownership, threat model e relatorios tecnicos.
- [`specs/`](specs/): prompts e contexto de analise aprofundada.

## Leitura recomendada por perfil

### Engenharia

1. [`getting-started.md`](getting-started.md)
2. [`api-e-operacao.md`](api-e-operacao.md)
3. [`arquitetura/01-visao-geral.md`](arquitetura/01-visao-geral.md)

### Lideranca tecnica

1. [`arquitetura/03-deploy.md`](arquitetura/03-deploy.md)
2. [`reports/security_best_practices.md`](reports/security_best_practices.md)
3. [`reports/threat-model.md`](reports/threat-model.md)

### Stakeholders e narrativa de produto

1. [`../presentation/index.html`](../presentation/index.html)
2. [`notebooklm/13-apresentacao-profissional.md`](notebooklm/13-apresentacao-profissional.md)

## Criterio de manutencao

- docs de entrada devem refletir comportamento real do codigo, nao plano futuro;
- detalhes operacionais longos ficam em `docs/`, nao no `README` raiz;
- quando houver conflito entre documento antigo e implementacao atual, vale a implementacao atual.
