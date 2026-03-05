-- Migração: adiciona campos de ocorrência e payload em snapshots_rotas
-- Aplicar no Supabase via SQL Editor

ALTER TABLE snapshots_rotas
  ADD COLUMN IF NOT EXISTS ocorrencia_principal text,
  ADD COLUMN IF NOT EXISTS observacao_resumo     text,
  ADD COLUMN IF NOT EXISTS payload_json          jsonb;

-- Popula ocorrencia_principal a partir do campo ocorrencia existente (retrocompatibilidade)
UPDATE snapshots_rotas
SET ocorrencia_principal = ocorrencia
WHERE ocorrencia_principal IS NULL AND ocorrencia IS NOT NULL AND ocorrencia <> '';

-- Popula observacao_resumo a partir do campo descricao existente (retrocompatibilidade)
UPDATE snapshots_rotas
SET observacao_resumo = descricao
WHERE observacao_resumo IS NULL AND descricao IS NOT NULL AND descricao <> '';
