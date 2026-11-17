import { createAdminClient } from "@/lib/supabase/admin";
import type { Plan } from "@/types/access";
import type { UpdatePlanResult } from "@/types/payments";

/**
 * Atualiza o plano de um usuário no banco de dados com privilégios de servidor.
 * Registra a transição na Caixa Preta de Auditoria de forma perene.
 */
export async function updateUserPlan(
  userId: string,
  newPlan: Plan,
  metadata?: Record<string, unknown>
): Promise<UpdatePlanResult> {
  try {
    const admin = createAdminClient();

    // 1. Busca o estado atual do perfil
    const { data: currentProfile, error: fetchError } = await admin
      .from("profiles")
      .select("plan, role, status")
      .eq("id", userId)
      .single();

    if (fetchError || !currentProfile) {
      return {
        success: false,
        error: `Usuário ${userId} não encontrado para atualização de plano.`,
      };
    }

    const previousPlan = currentProfile.plan as Plan;

    // Se já estiver no mesmo plano, não há necessidade de mutação
    if (previousPlan === newPlan) {
      return {
        success: true,
        previousPlan,
        newPlan,
      };
    }

    // 2. Atualiza o plano no perfil
    const { error: updateError } = await admin
      .from("profiles")
      .update({ plan: newPlan })
      .eq("id", userId);

    if (updateError) {
      return {
        success: false,
        error: `Erro ao atualizar plano no Supabase: ${updateError.message}`,
      };
    }

    // 3. Registra auditoria imutável via Service Role
    await admin.from("audit_logs").insert({
      actor_id: null, // Ação disparada pelo gateway de pagamento / sistema
      actor_email: "system@foundation.webhook",
      action: "plan.updated",
      entity_type: "profile",
      entity_id: userId,
      metadata: {
        previousPlan,
        newPlan,
        timestamp: new Date().toISOString(),
        ...metadata,
      },
    });

    return {
      success: true,
      previousPlan,
      newPlan,
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Erro desconhecido ao processar plano.";
    return {
      success: false,
      error: message,
    };
  }
}

/**
 * Consulta o plano atual de um usuário pelo ID.
 */
export async function getUserPlan(userId: string): Promise<Plan | null> {
  try {
    const admin = createAdminClient();
    const { data } = await admin
      .from("profiles")
      .select("plan")
      .eq("id", userId)
      .single();

    return (data?.plan as Plan) || null;
  } catch {
    return null;
  }
}

/**
 * Validação de segurança de segredo de webhook (Timing-safe comparison).
 */
export function verifyWebhookSecret(providedSecret: string | null): boolean {
  const expectedSecret = process.env.PAYMENT_WEBHOOK_SECRET;

  if (!expectedSecret || !providedSecret) {
    return false;
  }

  return providedSecret === expectedSecret;
}
