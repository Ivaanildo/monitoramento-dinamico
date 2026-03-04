# Prompt Inicial Para Comecar as Implementacoes

## Objetivo

Usar um prompt claro, restrito e executavel para iniciar o primeiro corte de implementacao sem abrir frentes paralelas desnecessarias.

## Prompt recomendado

```md
Quero iniciar a implementacao do primeiro corte definido em `docs/implementacoes/Incremento1_Estrutura_Tecnica.md`.

Trabalhe apenas na Ordem 1 e no inicio da Ordem 2.

Escopo exato desta execucao:
1. ajustar `projeto_zero_separado/config.yaml` para suportar o caminho configuravel de `rota_logistica.json`;
2. criar `projeto_zero_separado/core/rotas_corporativas.py`;
3. criar a base de `projeto_zero_separado/core/painel_service.py` somente com o adaptador de contrato necessario para viabilizar o primeiro corte;
4. expor `GET /rotas` e `GET /painel` no backend;
5. criar ou ajustar os testes minimos para validar:
   - carga das 20 rotas,
   - contrato basico de `/rotas`,
   - contrato basico de `/painel`.

Regras obrigatorias:
1. nao implemente auth ainda;
2. nao implemente persistencia ainda;
3. nao altere o frontend ainda;
4. nao avance para exportacao;
5. reaproveite o que ja existe em `projeto_zero_separado`;
6. leia antes os arquivos existentes e explique rapidamente o plano de edicao antes de modificar qualquer arquivo.

Criterio de conclusao desta execucao:
1. o backend deve conseguir responder `GET /rotas`;
2. o backend deve conseguir responder `GET /painel`;
3. os testes do primeiro corte devem existir e refletir os contratos minimos;
4. ao final, liste os arquivos alterados e os testes executados.
```

## Por que este prompt e o correto

1. Ele reduz o risco de abrir varias frentes ao mesmo tempo.
2. Ele força o inicio pelo backend, que hoje e o gargalo real de integracao.
3. Ele prende a execucao ao primeiro corte implementavel do plano.
4. Ele impede que auth, frontend e persistencia contaminem a primeira entrega tecnica.

## Prompt de continuidade depois do primeiro corte

Use este apenas depois que o primeiro corte estiver pronto:

```md
O primeiro corte do backend foi concluido.

Agora avance para a proxima etapa sem mexer em frontend ainda:
1. consolidar `core/painel_service.py`;
2. implementar `core/auth_local.py`;
3. adicionar `POST /auth/login`, `POST /auth/logout` e `GET /auth/session`;
4. proteger apenas os endpoints privados do painel;
5. expandir testes de auth e contrato.

Mantenha fora do escopo:
1. persistencia;
2. exportacao;
3. alteracoes no frontend.
```

## Observacao

Se voce quiser o maior controle possivel, sempre peça uma execucao por corte fechado:

1. primeiro backend minimo;
2. depois auth;
3. depois exportacao;
4. depois persistencia;
5. por ultimo frontend.
