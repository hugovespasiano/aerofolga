import { createClient } from "@supabase/supabase-js";

/**
 * Cliente com privilégios de Service Role (Admin).
 * Utilizado EXCLUSIVAMENTE em rotas de servidor (API / Webhooks)
 * para operações que exigem bypass seguro de RLS (ex: atualização de planos via webhook).
 *
 * NUNCA exponha esta chave nem importe este arquivo no frontend/client components.
 */
export function createAdminClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !serviceRoleKey) {
    throw new Error(
      "SUPABASE_SERVICE_ROLE_KEY ou NEXT_PUBLIC_SUPABASE_URL não configurados no ambiente do servidor."
    );
  }

  return createClient(url, serviceRoleKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
}
