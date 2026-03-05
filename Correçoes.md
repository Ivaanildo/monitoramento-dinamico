Plano de Refinamento Lógico (OBS, Ocorrência, Consistência Painel/Excel)
Resumo
Objetivo: padronizar comportamento entre card, detalhe e Excel; corrigir divergências de cálculo/fonte; e tornar a lógica de negócio explícita para ocorrência, observação e status.

Escopo fechado desta implementação:

Consistência de dados: detalhe abre por snapshot do mesmo ciclo do painel, com atualização manual em tempo real. ok

Regra de status híbrida: atraso por faixas + override por ocorrência grave/jam.

Observação operacional: texto resumido e contextual, sem mencionar jam factor no texto.
Ocorrência sempre preenchida (inclusive inferida quando houver congestionamento ou incidente explícito).
Correções de contrato backend/frontend (severidade, coordenadas, incidente_principal).

Gaps e divergências identificados (com origem no código)
Divergência de fonte entre painel e detalhe: painel usa snapshot de ciclo (painel_service.py, painel_service.py), enquanto detalhe consulta tempo real (app.py, PainelPage.tsx).
Ocorrência depende só de incidente principal; sem incidente fica vazia (painel_service.py), e no card nem renderiza badge se vazio (RouteCard.tsx).
Texto de observação ainda cita jam (contrário ao objetivo): (status.py).
Confiança em código (100/50/0) diverge da documentação (90/60/20 com penalidade) (status.py, CONTEXTO.md).
Contrato de incidente inconsistente:
Backend retorna latitude/longitude e severidade em rótulo PT-BR (here_incidents.py, here_incidents.py).
Frontend espera lat/lng e critical/major (MapView.tsx, MapView.tsx, ConsultaPage.tsx).
incidente_principal sai como objeto no backend, mas frontend tipa como string (consultor.py, ConsultaPage.tsx).
Especificação de implementação (decisão completa)
1. Regra de negócio unificada (status/ocorrência/observação)
Status base por atraso (Google):
Normal: atraso < 20.
Moderado: atraso >= 20 e <= 30.
Intenso: atraso > 30.
Sem Google válido: base = Sem dados.
Override por HERE/jam:
jam_max >= 10 ou road_closed: Parado.
jam_max >= 8: no mínimo Intenso.
jam_max >= 5: no mínimo Moderado.
Override por ocorrência:
Interdição: Parado.
Colisão/Acidente: no mínimo Intenso.
Bloqueio Parcial: no mínimo Moderado (ou Intenso se jam alto).
Ocorrência inferida:
Se não houver incidente explícito e (jam_max >= 5 ou atraso >= 15), definir ocorrencia_principal = "Engarrafamento".
Observação operacional (sem jam no texto):
Prioriza incidente com local/contexto.
Inclui atraso estimado.
Inclui resumo Google por zona (trecho inicial/central/final) quando houver lentidão.
Fluxo normal: frase curta de “sem anormalidades”.
Referência funcional já validada (cases antigos): [correlator.py](C:\Users\Administrador\Desktop\Automação Monitaramento de rotas Logisticas\monitor-rodovias\sources\correlator.py:752), [correlator.py](C:\Users\Administrador\Desktop\Automação Monitaramento de rotas Logisticas\monitor-rodovias\sources\correlator.py:765), [correlator.py](C:\Users\Administrador\Desktop\Automação Monitaramento de rotas Logisticas\monitor-rodovias\sources\correlator.py:846).

2. Persistência e consistência de ciclo
Worker continua gerando snapshot de ciclo (coletor.py, coletor.py).
Adicionar persistência de payload detalhado por rota no snapshot.
Migração SQL (com IF NOT EXISTS) em snapshots_rotas:
rota_id text
payload_json jsonb
ocorrencia_principal text
ocorrencias text
observacao_resumo text
índice (ciclo_id, rota_id).
Sem backfill obrigatório: para linhas antigas sem payload_json, endpoint snapshot retorna resumo e frontend exibe ação “Atualizar em tempo real”.
3. API e contratos públicos (mudanças aditivas)
GET /painel (manter compatibilidade):
adicionar ocorrencia_principal, ocorrencias, observacao_resumo, ciclo_id, dados_origem="snapshot".
Novo endpoint GET /rotas/{rota_id}/snapshot:
retorna payload detalhado do último ciclo da rota.
inclui dados_origem="snapshot" e ciclo_ts.
GET /rotas/{rota_id}/consultar permanece tempo real:
incluir dados_origem="realtime".
Normalização de incidentes:
retornar ambos lat/lng e latitude/longitude.
retornar severidade_codigo (critical|major|minor|low) além de severidade textual.
incidente_principal padronizado como objeto opcional com categoria, descricao, severidade.
4. Frontend (Painel + Consulta)
Painel:
manter carga via /painel (PainelPage.tsx).
card sempre mostra chip de ocorrência (Sem ocorrência quando vazio).
verso do card usa observacao_resumo.
Abertura de detalhe (“visão geral”):
abre Consulta em modo snapshot.
exibe badge “Dados do ciclo”.
Consulta:
primeira carga via /rotas/{id}/snapshot.
botão “Atualizar” troca para /rotas/{id}/consultar (tempo real), com badge “Tempo real”.
adaptar render para incidente_principal objeto.
aceitar severidade PT/EN e coordenadas em ambos formatos.
Mapa e lista de incidentes:
corrigir fallback de coordenadas (lat/lng -> latitude/longitude).
5. Excel/CSV
Reaproveitar colunas atuais em visão geral (excel_simple.py).
Relato passa a receber observação operacional padronizada (mesma do card), sem jam.
Estilos de ocorrência:
completar map para Condição Climática, Ocorrência, Sem ocorrência.
Cor da célula de ocorrência baseada em ocorrencia_principal (não no texto agregado quando múltiplo).
Remover truncamento agressivo do relato (ou elevar limite para 320+).
6. Testes e cenários de aceitação
Unitário backend (status.py):
faixas <20, 20-30, >30.
overrides por road_closed, Interdição, Colisão, Bloqueio Parcial.
inferência de Engarrafamento sem incidente.
Unitário observação:
incidente + atraso + zonas Google.
fluxo livre sem anormalidade.
sem menção a jam no texto.
Integração API:
/painel e /painel/exportar/excel com mesmos atraso_min para o mesmo ciclo.
/rotas/{id}/snapshot igual ao snapshot do painel.
/rotas/{id}/consultar pode divergir, mas com dados_origem="realtime".
Frontend:
card renderiza ocorrência mesmo vazia (fallback).
Consulta renderiza incidente_principal sem [object Object].
marcador de incidente aparece quando só houver latitude/longitude.
Regressão exportação:
coluna ocorrência preenchida para casos inferidos.
estilos aplicados por categoria.
7. Critérios objetivos de pronto
Clicando “ver obs.” no card, o texto segue padrão operacional e não exibe jam factor.
Clicando “visão geral”, o primeiro valor de atraso bate com painel/Excel do mesmo ciclo.
Ocorrência aparece em card e Excel para congestionamento inferido (sem incidente explícito).
Divergência entre snapshot e tempo real só acontece após ação explícita de atualização.
Todos os testes novos passam e sem quebra de endpoints existentes.
Assumptions e defaults escolhidos
Detalhe híbrido: snapshot primeiro, tempo real só por ação do usuário.
Regra de status híbrida adotada (faixas de atraso + override de ocorrência/jam).
Texto de observação em formato operacional, sem jam factor textual.
Mudanças de API são aditivas e retrocompatíveis.
Histórico antigo sem payload_json não será reprocessado; fallback de UI cobre esse caso.