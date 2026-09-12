-- HealthSurge AI — Supabase PostgreSQL Schema
-- Run this in the Supabase SQL Editor (Dashboard > SQL)

-- ── simulation_runs ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS simulation_runs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    seed            integer NOT NULL,
    status          text NOT NULL DEFAULT 'pending',
    forecast_utility       numeric(8, 6),
    service_utility        numeric(8, 6),
    worst_district_utility numeric(8, 6),
    total_unmet     integer,
    runtime_seconds numeric(8, 4),
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- ── district_results ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS district_results (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id   uuid NOT NULL REFERENCES simulation_runs(id) ON DELETE CASCADE,
    district_index  integer NOT NULL,
    capacity        integer NOT NULL,
    total_demand    integer NOT NULL,
    total_forecast_error numeric(10, 4),
    total_unmet     integer NOT NULL,
    service_utility numeric(8, 6),
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_district_results_sim_id ON district_results(simulation_id);

-- ── monthly_results ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS monthly_results (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id   uuid NOT NULL REFERENCES simulation_runs(id) ON DELETE CASCADE,
    month           integer NOT NULL,
    district_index  integer NOT NULL,
    forecast        numeric(10, 4),
    actual_demand   integer,
    capacity        integer,
    allocation      integer,
    unmet_demand    integer,
    anomaly_score   numeric(10, 4),
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_monthly_results_sim_id ON monthly_results(simulation_id);
CREATE INDEX IF NOT EXISTS idx_monthly_results_month  ON monthly_results(simulation_id, month);

-- ── ai_insights ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_insights (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id   uuid NOT NULL REFERENCES simulation_runs(id) ON DELETE CASCADE,
    summary         text,
    risks           text,
    recommendations text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_insights_sim_id ON ai_insights(simulation_id);

-- ── Row-Level Security ───────────────────────────────────────────────────────
-- Enable RLS so anonymous browser requests cannot read/write directly.
-- The Next.js server uses the service-role key which bypasses RLS.
ALTER TABLE simulation_runs  ENABLE ROW LEVEL SECURITY;
ALTER TABLE district_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE monthly_results  ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_insights      ENABLE ROW LEVEL SECURITY;

-- Allow the service role to do everything (RLS bypass is automatic for service role,
-- but explicit policies make intent clear):
-- No anon policies → browser cannot access data directly.
-- All access is mediated through Next.js server-side API routes.
