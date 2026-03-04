# Relatório de Validação de Falsos Positivos

> Data da validação: 2026-03-02  
> Escopo: conferir se o pipeline HERE ainda deixa passar incidentes indevidos após a correção de `Interdição` e do filtro semântico por rodovia.

---

## Resumo executivo

Na amostra validada com dados reais, **não houve falso positivo no resultado final retornado pelo sistema**.

O comportamento observado foi:

- em rotas curtas/médias, a HERE retornou incidentes brutos, mas o filtro semântico por `rodovia_logica` descartou todos os casos indevidos
- os descartes ocorreram apenas por:
  - ausência de código de rodovia explícito (`sem_codigo`)
  - código de rodovia incompatível com a rota (`rodovia_divergente`)
- em rotas longas, a validação ficou **parcialmente limitada** porque a HERE respondeu `400` no `corridor`, resultando em ausência de incidentes utilizáveis para confronto

Conclusão operacional: a correção está funcionando na amostra que efetivamente retornou incidentes HERE brutos. O principal bloqueador remanescente para ampliar a validação é a instabilidade da HERE em corredores longos.

---

## Metodologia

Foram executadas duas amostras:

1. **Amostra longa (stress / rotas críticas históricas)**  
   Rotas: `R01`, `R08`, `R14`, `R17`

2. **Amostra curta/média (validação com retorno HERE utilizável)**  
   Rotas: `R03`, `R13`, `R16`, `R20`

Critério usado para marcar um incidente como suspeito:

- incidente retornado no payload final sem código explícito de rodovia, embora a rota possua `rodovia_logica` reconhecível
- incidente retornado no payload final com rodovia divergente da rota
- `Interdição` sem `bloqueio_escopo=total`
- `Bloqueio Parcial` sem `bloqueio_escopo=parcial`

---

## Resultado da amostra longa

### Rotas avaliadas

| Rota | Rodovia lógica | Resultado |
|---|---|---|
| `R01` | `BR-116`, `BR-101` | HERE sem dados utilizáveis |
| `R08` | `BR-116` | HERE sem dados utilizáveis |
| `R14` | `BR-116`, `BR-101` | HERE sem dados utilizáveis |
| `R17` | `BR-101` | HERE sem dados utilizáveis |

### Observações

- Nessas rotas, a HERE respondeu `400` nas chamadas de `incidents` e/ou `flow` com `corridor`.
- Como consequência, o sistema terminou com `0` incidentes HERE nessas consultas.
- Isso evita falso positivo no payload final, mas **não permite validar semanticamente** se haveria descartes corretos ou incorretos, porque o provedor não entregou incidentes brutos para confronto.

### Risco residual

- A correção de falso positivo não foi contrariada nessa amostra.
- Porém, a ausência de dados HERE em rotas longas impede afirmar cobertura completa para esse grupo.

---

## Resultado da amostra curta/média

### Comparativo bruto vs filtrado

| Rota | Rodovia lógica | Incidentes HERE brutos | Mantidos no payload final | Descartados |
|---|---|---:|---:|---:|
| `R03` | `BR-116 (Dutra)` | 10 | 0 | 10 |
| `R13` | `BR-101`, `BR-376` | 3 | 0 | 3 |
| `R16` | `BR-101` | 0 | 0 | 0 |
| `R20` | `BR-101` | 1 | 0 | 1 |
| **Total** | — | **14** | **0** | **14** |

### Motivos de descarte consolidados

| Motivo | Quantidade |
|---|---:|
| `sem_codigo` | 11 |
| `rodovia_divergente` | 3 |

### Interpretação

- Nenhum dos 14 incidentes brutos passou para o payload final porque nenhum atendia ao critério semântico de rodovia da rota.
- Isso é consistente com o objetivo da correção: eliminar ruído urbano/local ou incidentes de outra BR que entram no `corridor` apenas por proximidade geométrica.

---

## Evidências representativas dos descartes

### `R03` — São Paulo (Cajamar) -> Rio de Janeiro (Pavuna)

Casos descartados:

- `Interdição` com descrição `Fechado | Estrada fechada`  
  Motivo: `sem_codigo`  
  Leitura: há indicação de fechamento, mas sem BR explícita; antes isso poderia contaminar a rota, agora não entra.

- `Engarrafamento` em `Av Doutor Peixoto De Castro`  
  Motivo: `sem_codigo`  
  Leitura: ocorrência urbana/local, sem evidência textual de `BR-116`.

- `Engarrafamento` em `BR-010/Av Takara Belmont`  
  Motivo: `rodovia_divergente`  
  Leitura: o incidente cita rodovia, mas não a rodovia lógica da rota (`BR-116`).

### `R13` — Santa Catarina (GCR) -> Paraná (Curitiba)

Casos descartados:

- `Engarrafamento` em `Rua Demósthenes Feminella`  
  Motivo: `sem_codigo`

- `Engarrafamento` em `BR-280/Saída 58A/Saída 58B`  
  Motivo: `rodovia_divergente`

- `Engarrafamento` em `Rua Guaramirim`  
  Motivo: `sem_codigo`

### `R20` — Rio Grande do Sul (Sapucaia) -> Santa Catarina (GCR)

Caso descartado:

- `Engarrafamento` em `Rua Sílvio Burigo`  
  Motivo: `sem_codigo`

---

## Verificação de falso positivo no payload final

Na amostra validada:

- **0 incidentes** foram retornados no payload final contendo:
  - rodovia ausente quando a rota tinha `rodovia_logica` reconhecível
  - rodovia divergente da rota
  - `Interdição` sem `bloqueio_escopo=total`
  - `Bloqueio Parcial` inconsistente

Portanto, **nenhum falso positivo foi observado no dado final gerado** dentro da amostra em que a HERE forneceu incidentes brutos.

---

## Limitações encontradas

### 1. Erro `400` da HERE em corredores longos

Em rotas maiores, a HERE ainda falha com `400` no `corridor`, o que reduz a capacidade de auditoria real do resultado.

Impacto:

- o sistema não recebe incidentes HERE para essas rotas
- a análise de falso positivo fica limitada porque não há massa de dados bruta para confronto

### 2. Mensagem de erro agregada do `consultor`

Quando a coleta HERE falha antes de retornar payload estruturado, o campo `erros.here` pode aparecer como `API key não configurada`, embora a chave exista e o problema real seja falha de coleta/timeout.

Impacto:

- o diagnóstico operacional pode induzir a interpretação errada da falha

### 3. Ruído de log por encoding no terminal

Foram observados erros de `UnicodeEncodeError` ao imprimir logs com `→` no console `cp1252`.

Impacto:

- não afeta a lógica de filtragem
- atrapalha a leitura dos logs durante validação manual

---

## Conclusão

Com base na coleta real executada em 2026-03-02:

- a correção de filtro semântico por rodovia **está impedindo a entrada de incidentes urbanos e de rodovias divergentes** no payload final
- a correção de classificação **não apresentou casos de `Interdição` indevida** na amostra validada
- **não foram encontrados falsos positivos no dado final gerado**

O principal ponto pendente não é a regra de filtro em si, e sim a confiabilidade da coleta HERE em rotas longas, que ainda precisa ser tratada para ampliar a validação em produção.

---

## Próximos passos recomendados

1. Corrigir a estratégia de `corridor` para rotas longas (reduzir tamanho efetivo da query ou forçar fallback controlado) e repetir a validação nas rotas `R01`, `R08`, `R14` e `R17`.
2. Ajustar o campo `erros.here` no `consultor` para distinguir `API key ausente` de `falha de coleta`.
3. Remover caracteres incompatíveis com `cp1252` dos logs de console para evitar ruído durante auditoria operacional.
