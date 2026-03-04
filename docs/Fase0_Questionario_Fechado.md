# Fase 0 - Questionario Fechado de Decisao

## Como responder

Marque apenas uma opcao por pergunta.

Formato sugerido de resposta:

`Q01: A`
`Q02: B`
`Q03: A`

Se quiser, voce pode adicionar uma observacao curta em qualquer item.

---

## Q01. Qual e o produto principal da primeira entrega?

- [ ] A. Consulta on-demand por rota individual
- [ ] B. Painel de monitoramento continuo de rotas fixas
- [ ] C. Entrega hibrida com os dois fluxos desde o inicio

## Q02. A "Visao Geral" de rotas fixas entra na primeira versao?

- [ ] A. Nao, primeira versao so com consulta individual
- [ ] B. Sim, mas como modulo simples complementar
- [ ] C. Sim, e ela sera o foco principal

## Q03. Qual backend sera a base oficial do produto?

- [ ] A. `projeto_zero_separado`
- [ ] B. `Automacao Monitaramento de rotas Logisticas/monitor-rodovias`
- [ ] C. Novo backend unificado criado do zero

## Q04. Qual sera o papel do `monitor-rodovias` nesta fase?

- [ ] A. Referencia funcional e fonte de regras legadas
- [ ] B. Base principal de execucao
- [ ] C. Apenas arquivo historico, sem reaproveitamento relevante

## Q05. O Supabase entra no escopo agora?

- [ ] A. Nao, fica fora da primeira entrega
- [ ] B. Entra apenas para persistencia basica
- [ ] C. Entra completo com persistencia, auth e realtime

## Q06. O sistema precisa de autenticacao na primeira entrega?

- [ ] A. Nao
- [ ] B. Sim, autenticacao simples interna
- [ ] C. Sim, com fluxo completo de usuarios desde ja

## Q07. Quais fontes de dados entram na primeira versao?

- [ ] A. HERE + Google
- [ ] B. HERE + Google + TomTom
- [ ] C. HERE apenas

## Q08. Qual frontend sera a interface oficial inicial?

- [ ] A. `projeto_zero_separado/web/static/index.html`
- [ ] B. `Automacao Monitaramento de rotas Logisticas/monitor-rodovias/frontend`
- [ ] C. `Frontend/Criar frontend dinamico`

## Q09. Se o frontend oficial for o novo Vite/React, qual sera a estrategia?

- [ ] A. Primeiro integrar com a API real e manter escopo funcional minimo
- [ ] B. Primeiro finalizar o design e depois integrar
- [ ] C. Adiar esse frontend para outra fase

## Q10. O frontend novo hoje deve ser tratado como:

- [ ] A. Base visual a ser adaptada para producao
- [ ] B. Referencia estetica, sem compromisso com a estrutura atual
- [ ] C. Material descartavel, sem reaproveitamento

## Q11. Qual sera a fonte oficial das rotas predefinidas?

- [ ] A. `projeto_zero_separado/favoritos.json`
- [ ] B. `Automacao Monitaramento de rotas Logisticas/monitor-rodovias/rota_logistica.json`
- [ ] C. Novo arquivo consolidado a ser criado

## Q12. Como tratar "favoritos" e "rotas corporativas"?

- [ ] A. Manter separados
- [ ] B. Unificar em um unico cadastro
- [ ] C. Ignorar favoritos agora e focar so em rotas corporativas

## Q13. Waypoints obrigatorios (`via`) entram como requisito obrigatorio agora?

- [ ] A. Sim, obrigatorio ja na primeira entrega
- [ ] B. Sim, mas apenas para rotas predefinidas
- [ ] C. Nao, fica para fase posterior

## Q14. O contrato principal da aplicacao nesta fase sera:

- [ ] A. `ResultadoRota` detalhado por consulta
- [ ] B. Payload agregado de dashboard multi-rotas
- [ ] C. Ambos, ja definidos desde a primeira entrega

## Q15. Qual exportacao entra na primeira entrega?

- [ ] A. Apenas exportacao de rota individual
- [ ] B. Rota individual + visao geral
- [ ] C. Nenhuma exportacao agora

## Q16. Qual e o ambiente alvo inicial?

- [ ] A. Execucao local / servidor interno
- [ ] B. Deploy web interno com acesso controlado
- [ ] C. Deploy cloud completo desde o inicio

## Q17. Historico de ciclos e comparacao temporal entram agora?

- [ ] A. Nao, foco em decisao em tempo real
- [ ] B. Sim, historico minimo
- [ ] C. Sim, historico completo e comparativo

## Q18. Qual e o criterio principal de sucesso da primeira entrega?

- [ ] A. Consultar uma rota com precisao e visualizar corretamente no mapa
- [ ] B. Validar rotas criticas com waypoints obrigatorios
- [ ] C. Entregar painel consolidado multi-rotas em operacao

## Q19. O que fica explicitamente fora da primeira entrega?

- [ ] A. Login, realtime e deploy cloud
- [ ] B. Apenas realtime e historico
- [ ] C. Nada fica fora; queremos estrutura completa desde ja

## Q20. Quem e o usuario primario da primeira versao?

- [ ] A. Operacao logistica / torre de monitoramento
- [ ] B. Gestao de risco
- [ ] C. Lideranca / visao executiva

---

## Gabarito Tecnico Recomendado

Se a meta for ganhar direcao rapida com menor risco tecnico, a combinacao mais pragmatica e:

`Q01: A`
`Q02: B`
`Q03: A`
`Q04: A`
`Q05: A`
`Q06: A`
`Q07: A`
`Q08: C`
`Q09: A`
`Q10: A`
`Q11: C`
`Q12: A`
`Q13: A`
`Q14: A`
`Q15: B`
`Q16: A`
`Q17: A`
`Q18: B`
`Q19: A`
`Q20: A`

Esse conjunto prioriza:

- consolidar primeiro o nucleo funcional,
- reduzir dependencias externas desnecessarias nesta fase,
- e estruturar o frontend novo em cima de um backend unico e estavel.
