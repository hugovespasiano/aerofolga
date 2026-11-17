import { createClient } from "@/lib/supabase/server";
import type { AuditLog, CreateAuditLogInput } from "@/types/audit";

/**
 * Registra um evento imutável na Caixa Preta de Auditoria.
 * Extrai a identidade confiável do autor diretamente da sessão SSR.
 */
export async function logAuditEvent(
  input: CreateAuditLogInput
): Promise<{ success: boolean; logId?: string; error?: string }> {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    const { data, error } = await supabase
      .from("audit_logs")
      .insert({
        organization_id: input.organizationId || null,
        actor_id: user?.id || null,
        actor_email: user?.email || null,
        action: input.action,
        entity_type: input.entityType,
        entity_id: input.entityId || null,
        metadata: input.metadata || {},
      })
      .select("id")
      .single();

    if (error || !data) {
      return { success: false, error: error?.message || "Erro ao registrar auditoria." };
    }

    return { success: true, logId: data.id };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Erro desconhecido na auditoria.";
    return { success: false, error: message };
  }
}

/**
 * Consulta os logs de auditoria de uma organização específica.
 * RLS garante que apenas admins ou owners da organização tenham acesso.
 */
export async function getOrganizationAuditLogs(
  organizationId: string,
  limit: number = 50
): Promise<AuditLog[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("audit_logs")
    .select("*")
    .eq("organization_id", organizationId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error || !data) {
    return [];
  }

  return data as AuditLog[];
}

/**
 * Consulta global de logs da plataforma.
 * RLS garante que apenas Super-Admins (com audit.view_all) tenham acesso.
 */
export async function getGlobalAuditLogs(limit: number = 50): Promise<AuditLog[]> {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("audit_logs")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error || !data) {
    return [];
  }

  return data as AuditLog[];
}
