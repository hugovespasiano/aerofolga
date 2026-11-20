-- ==============================================================================
-- AEROFOLGA — FOUNDATION ALIGNMENT & SECURITY HARDENING (MIGRATION 0002)
-- Baseado no contrato arquitetural do meu-template-base (Vespasiano Labs)
-- ==============================================================================

-- 1. Tabela Canônica de Perfis de Usuário (Substrato Universal de Identidade)
CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name text,
  role text NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  plan text NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'premium')),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own display_name" ON public.profiles
  FOR UPDATE USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Trigger para provisionar public.profiles automaticamente após cadastro no Supabase Auth
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name, role, plan, status)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
    'user',
    'free',
    'active'
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 2. Tabelas de Permissões e Perfis da Fundação
CREATE TABLE IF NOT EXISTS public.permissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  description text,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.permissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read permissions" ON public.permissions FOR SELECT USING (true);

CREATE TABLE IF NOT EXISTS public.role_permissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  role text NOT NULL,
  permission_id uuid NOT NULL REFERENCES public.permissions(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_role_permission UNIQUE (role, permission_id)
);

ALTER TABLE public.role_permissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read role_permissions" ON public.role_permissions FOR SELECT USING (true);

-- Inserir permissões básicas
INSERT INTO public.permissions (name, description) VALUES
  ('flights.search', 'Permissão para pesquisar voos no radar'),
  ('deals.view', 'Permissão para visualizar promoções auditadas'),
  ('couples.manage', 'Permissão para gerenciar calendário do casal')
ON CONFLICT (name) DO NOTHING;

INSERT INTO public.role_permissions (role, permission_id)
SELECT 'user', id FROM public.permissions WHERE name IN ('flights.search', 'deals.view', 'couples.manage')
ON CONFLICT DO NOTHING;

INSERT INTO public.role_permissions (role, permission_id)
SELECT 'admin', id FROM public.permissions
ON CONFLICT DO NOTHING;

-- 3. Tabela de Auditoria Imutável (Caixa Preta de Governança)
CREATE TABLE IF NOT EXISTS public.audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid,
  actor_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  actor_email text,
  action text NOT NULL,
  entity_type text NOT NULL,
  entity_id text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Usuários comuns podem visualizar apenas suas próprias ações
CREATE POLICY "Users can read own audit logs" ON public.audit_logs
  FOR SELECT USING (auth.uid() = actor_id);

-- 4. Tabela de Idempotência Mandatória para Webhooks Financeiros
CREATE TABLE IF NOT EXISTS public.processed_webhook_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  gateway text NOT NULL,                  -- 'stripe', 'asaas', 'mercadopago', 'manual'
  event_id text NOT NULL,                 -- Identificador único do evento no gateway
  event_type text NOT NULL,               -- 'charge.succeeded', 'subscription.updated'
  status text NOT NULL DEFAULT 'success' CHECK (status IN ('processing', 'success', 'failed')),
  payload jsonb,
  processed_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_gateway_event_id UNIQUE (gateway, event_id)
);

ALTER TABLE public.processed_webhook_events ENABLE ROW LEVEL SECURITY;

-- Índices de Performance
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_plan ON public.profiles(plan);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON public.audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON public.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_webhook_gateway_event ON public.processed_webhook_events(gateway, event_id);
