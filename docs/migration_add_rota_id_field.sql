-- Migração: adiciona campo rota_id em snapshots_rotas
-- Aplicar no Supabase via SQL Editor (após migration_add_ocorrencia_fields.sql)

ALTER TABLE snapshots_rotas
  ADD COLUMN IF NOT EXISTS rota_id text;

-- Cria índice para acelerar o endpoint GET /rotas/{rota_id}/snapshot
CREATE INDEX IF NOT EXISTS idx_snapshots_rotas_rota_id_ts
  ON snapshots_rotas (rota_id, ts_iso DESC);
