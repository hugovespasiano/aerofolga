-- ==============================================================================
-- AEROFOLGA — CORE SCHEMA & CONSTITUTIONAL POLICIES (MIGRATION 0001)
-- Baseado na Governança do meu-template-base e Protocolo SECURITY_AGENT.md
-- ==============================================================================

-- 1. Tabela de Municípios e Prefeituras Canônicas
CREATE TABLE IF NOT EXISTS public.cities_canonical (
  id text PRIMARY KEY,
  name text NOT NULL,
  state text NOT NULL DEFAULT 'RJ',
  institution_name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Ativar RLS e permitir leitura pública para seleção de cidades no frontend
ALTER TABLE public.cities_canonical ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read-only access for canonical cities" ON public.cities_canonical
  FOR SELECT USING (true);

-- Inserir dados padrão do Sul Fluminense
INSERT INTO public.cities_canonical (id, name, state, institution_name) VALUES
  ('resende', 'Resende', 'RJ', 'Prefeitura Municipal de Resende'),
  ('barra_mansa', 'Barra Mansa', 'RJ', 'Prefeitura Municipal de Barra Mansa'),
  ('itatiaia', 'Itatiaia', 'RJ', 'Prefeitura Municipal de Itatiaia'),
  ('volta_redonda', 'Volta Redonda', 'RJ', 'Prefeitura Municipal de Volta Redonda'),
  ('porto_real', 'Porto Real', 'RJ', 'Prefeitura Municipal de Porto Real'),
  ('pirai', 'Piraí', 'RJ', 'Prefeitura Municipal de Piraí'),
  ('quatis', 'Quatis', 'RJ', 'Prefeitura Municipal de Quatis')
ON CONFLICT (id) DO NOTHING;

-- 2. Tabela de Feriados Municipais
CREATE TABLE IF NOT EXISTS public.municipal_holidays (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  city_id text NOT NULL REFERENCES public.cities_canonical(id) ON DELETE CASCADE,
  day integer NOT NULL CHECK (day BETWEEN 1 AND 31),
  month integer NOT NULL CHECK (month BETWEEN 1 AND 12),
  name text NOT NULL,
  type text NOT NULL CHECK (type IN ('emancipacao', 'padroeiro', 'tradicional', 'decreto_emergencial')),
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.municipal_holidays ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read-only access for municipal holidays" ON public.municipal_holidays
  FOR SELECT USING (true);

-- Inserir feriados municipais canônicos do Sul Fluminense
INSERT INTO public.municipal_holidays (city_id, day, month, name, type) VALUES
  ('resende', 29, 9, 'Aniversário de Resende', 'emancipacao'),
  ('resende', 24, 6, 'Dia de São João Batista', 'padroeiro'),
  ('barra_mansa', 3, 10, 'Aniversário de Barra Mansa', 'emancipacao'),
  ('barra_mansa', 20, 1, 'Dia de São Sebastião', 'padroeiro'),
  ('itatiaia', 1, 6, 'Emancipação de Itatiaia', 'emancipacao'),
  ('itatiaia', 19, 3, 'Dia de São José', 'padroeiro'),
  ('volta_redonda', 17, 7, 'Aniversário de Volta Redonda', 'emancipacao'),
  ('volta_redonda', 13, 6, 'Dia de Santo Antônio', 'padroeiro');

-- 3. Tabela de Decretos de Diário Oficial e Eventos Atípicos (Rock in Rio, Clima, etc.)
CREATE TABLE IF NOT EXISTS public.official_gazette_notices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  city_id text REFERENCES public.cities_canonical(id) ON DELETE CASCADE,
  is_state_rj boolean NOT NULL DEFAULT false,
  notice_date date NOT NULL,
  title text NOT NULL,
  description text,
  gazette_source_url text,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.official_gazette_notices ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read-only access for gazette notices" ON public.official_gazette_notices
  FOR SELECT USING (true);

-- 4. Perfis de Casal / Usuários do App
CREATE TABLE IF NOT EXISTS public.couples_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  user_name text NOT NULL,
  user_city_id text NOT NULL REFERENCES public.cities_canonical(id),
  user_tre_leave_days integer NOT NULL DEFAULT 0,
  
  partner_name text NOT NULL,
  partner_city_id text NOT NULL REFERENCES public.cities_canonical(id),
  partner_bank_hours_days integer NOT NULL DEFAULT 0,
  
  notification_channel text NOT NULL DEFAULT 'whatsapp' CHECK (notification_channel IN ('whatsapp', 'telegram', 'email')),
  whatsapp_number text,
  telegram_chat_id text,
  notifications_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.couples_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own couple profile" ON public.couples_profiles
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- 5. Janelas Mútuas Detectadas
CREATE TABLE IF NOT EXISTS public.detected_windows (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  couple_id uuid NOT NULL REFERENCES public.couples_profiles(id) ON DELETE CASCADE,
  start_date date NOT NULL,
  end_date date NOT NULL,
  total_days integer NOT NULL,
  nights integer NOT NULL,
  description text NOT NULL,
  reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  is_alerted boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.detected_windows ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view detected windows of their profile" ON public.detected_windows
  FOR ALL USING (
    EXISTS (SELECT 1 FROM public.couples_profiles cp WHERE cp.id = detected_windows.couple_id AND cp.user_id = auth.uid())
  );

-- 6. Tabela de Oportunidades de Voos Auditadas (Radar Tilli + Resolução 400 ANAC)
CREATE TABLE IF NOT EXISTS public.flight_deals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  window_id uuid REFERENCES public.detected_windows(id) ON DELETE CASCADE,
  origin_iata text NOT NULL,
  destination_iata text NOT NULL,
  airline text NOT NULL,
  flight_type text NOT NULL CHECK (flight_type IN ('direct', 'connection_human', 'hidden_city')),
  connection_time_minutes integer DEFAULT 0,
  typical_price numeric(10, 2) NOT NULL,
  promo_price numeric(10, 2) NOT NULL,
  discount_percentage numeric(5, 2) NOT NULL,
  booking_url text NOT NULL,
  anac_protection_acknowledged boolean NOT NULL DEFAULT true,
  found_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.flight_deals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view deals linked to their windows" ON public.flight_deals
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.detected_windows dw
      JOIN public.couples_profiles cp ON cp.id = dw.couple_id
      WHERE dw.id = flight_deals.window_id AND cp.user_id = auth.uid()
    )
  );

-- Índices Estratégicos para Buscas Rápidas
CREATE INDEX IF NOT EXISTS idx_couples_profiles_user ON public.couples_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_detected_windows_dates ON public.detected_windows(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_municipal_holidays_city ON public.municipal_holidays(city_id);
CREATE INDEX IF NOT EXISTS idx_flight_deals_discount ON public.flight_deals(discount_percentage DESC);
