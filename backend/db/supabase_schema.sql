-- =====================================================================
-- DebugVerse Supabase Database Schema (Production Ready & Fully Idempotent)
-- Run this in the Supabase SQL Editor:
-- https://app.supabase.com → Your Project → SQL Editor → New Query
-- =====================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── 1. Subscriptions ─────────────────────────────────────────────────────────
-- Tracks Stripe billing tiers per user.
-- Supabase Auth handles the users table (auth.users).
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  stripe_customer_id      text,
  stripe_subscription_id  text UNIQUE,
  tier                    text NOT NULL DEFAULT 'free'
                          CHECK (tier IN ('free', 'pro', 'enterprise')),
  status                  text NOT NULL DEFAULT 'active'
                          CHECK (status IN ('active', 'inactive', 'cancelled', 'past_due')),
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now()
);

-- Index for fast tier lookups by user_id
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);

-- Enable RLS
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- Idempotent RLS Policies
-- Note: Supabase's service_role key has BYPASSRLS enabled by default.
DROP POLICY IF EXISTS "Users can view own subscription" ON public.subscriptions;
CREATE POLICY "Users can view own subscription" ON public.subscriptions
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own subscription" ON public.subscriptions;
CREATE POLICY "Users can insert own subscription" ON public.subscriptions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own subscription" ON public.subscriptions;
CREATE POLICY "Users can update own subscription" ON public.subscriptions
  FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role full access" ON public.subscriptions;
CREATE POLICY "Service role full access" ON public.subscriptions
  TO service_role USING (true) WITH CHECK (true);


-- ── 2. Debug Sessions ─────────────────────────────────────────────────────────
-- Persistent debug history, replacing localStorage.
CREATE TABLE IF NOT EXISTS public.debug_sessions (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  language         text NOT NULL,
  code             text NOT NULL,
  ai_response      text,
  raw_markdown     text,
  model_used       text,
  rag_citations    jsonb DEFAULT '[]'::jsonb,
  routing_info     jsonb DEFAULT '{}'::jsonb,
  execution_output text,
  created_at       timestamptz NOT NULL DEFAULT now()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_debug_sessions_user_id ON public.debug_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_debug_sessions_created_at ON public.debug_sessions(created_at DESC);

-- Enable RLS
ALTER TABLE public.debug_sessions ENABLE ROW LEVEL SECURITY;

-- Idempotent RLS Policies
DROP POLICY IF EXISTS "Users can manage own debug sessions" ON public.debug_sessions;
CREATE POLICY "Users can manage own debug sessions" ON public.debug_sessions
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role full access" ON public.debug_sessions;
CREATE POLICY "Service role full access" ON public.debug_sessions
  TO service_role USING (true) WITH CHECK (true);


-- ── 3. Usage Events ───────────────────────────────────────────────────────────
-- Tracks all billable events for analytics and rate limiting fallback.
CREATE TABLE IF NOT EXISTS public.usage_events (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid,  -- nullable to support anonymous/pre-auth activity
  event_type      text NOT NULL
                  CHECK (event_type IN ('debug', 'execute', 'chat', 'rag_index')),
  model_used      text,
  tokens_used     integer DEFAULT 0,
  language        text,
  session_id      text,
  ip_hash         text,  -- SHA256 hash of IP for privacy-safe analytics
  created_at      timestamptz NOT NULL DEFAULT now()
);

-- Indexes for analytics queries and rate limit checks
CREATE INDEX IF NOT EXISTS idx_usage_events_user_id ON public.usage_events(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_events_created_at ON public.usage_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_events_user_date ON public.usage_events(user_id, created_at DESC);

-- Enable RLS
ALTER TABLE public.usage_events ENABLE ROW LEVEL SECURITY;

-- Idempotent RLS Policies
DROP POLICY IF EXISTS "Users can view own usage" ON public.usage_events;
CREATE POLICY "Users can view own usage" ON public.usage_events
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role full access" ON public.usage_events;
CREATE POLICY "Service role full access" ON public.usage_events
  TO service_role USING (true) WITH CHECK (true);


-- ── 4. Auto-update `updated_at` trigger ──────────────────────────────────────
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS subscriptions_updated_at ON public.subscriptions;
CREATE TRIGGER subscriptions_updated_at
  BEFORE UPDATE ON public.subscriptions
  FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();


-- ── 5. Analytics Views ────────────────────────────────────────────────────────
-- Daily usage summary per user (useful for dashboards)
CREATE OR REPLACE VIEW public.daily_usage_summary AS
SELECT
  user_id,
  DATE(created_at) AS date,
  event_type,
  COUNT(*) AS event_count,
  SUM(tokens_used) AS total_tokens
FROM public.usage_events
GROUP BY user_id, DATE(created_at), event_type;

-- ── DONE ───────────────────────────────────────────────────────────────────────
-- After running this schema:
-- 1. Go to Supabase Dashboard → Authentication → Settings:
--    - Enable Email/Password sign-in
--    - Enable Google OAuth (optional)
-- 2. Copy Project URL, Anon Key, and Service Role Key into backend/.env & frontend/.env
-- 3. Restart the backend server

