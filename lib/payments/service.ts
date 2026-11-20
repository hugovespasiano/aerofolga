import crypto from "crypto";
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
      .update({ plan: newPlan, updated_at: new Date().toISOString() })
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
 * Validação de segurança de segredo estático em tempo constante (Timing-Safe Comparison).
 * Mitiga ataques de temporização (Timing Attacks).
 */
export function verifyWebhookSecret(providedSecret: string | null): boolean {
  const expectedSecret = process.env.PAYMENT_WEBHOOK_SECRET;

  if (!expectedSecret || !providedSecret) {
    return false;
  }

  try {
    const expectedBuffer = Buffer.from(expectedSecret, "utf-8");
    const providedBuffer = Buffer.from(providedSecret, "utf-8");

    if (expectedBuffer.length !== providedBuffer.length) {
      return false;
    }

    return crypto.timingSafeEqual(expectedBuffer, providedBuffer);
  } catch {
    return false;
  }
}

/**
 * Validação criptográfica de assinatura HMAC-SHA256 sobre o raw body em tempo constante.
 * Suporta formatos Stripe, Asaas e padrões Webhook seguros (RFC 2104).
 */
export function verifyWebhookHmacSignature(
  rawBody: string,
  signature: string | null,
  secretOverride?: string
): boolean {
  const secret = secretOverride || process.env.PAYMENT_WEBHOOK_SECRET;
  if (!secret || !signature) {
    return false;
  }

  try {
    const cleanSignature = signature.startsWith("sha256=")
      ? signature.slice(7)
      : signature;

    const computedHash = crypto
      .createHmac("sha256", secret)
      .update(rawBody, "utf-8")
      .digest("hex");

    const expectedBuffer = Buffer.from(computedHash, "hex");
    const providedBuffer = Buffer.from(cleanSignature, "hex");

    if (expectedBuffer.length !== providedBuffer.length) {
      return false;
    }

    return crypto.timingSafeEqual(expectedBuffer, providedBuffer);
  } catch {
    return false;
  }
}

/**
 * Validação de janela temporal para neutralizar ataques de repetição (Anti-Replay Attack).
 * Janela padrão: tolerância máxima de 300 segundos (5 minutos).
 */
export function isTimestampValid(
  timestampSec: number | string | null,
  maxToleranceSec: number = 300
): boolean {
  if (!timestampSec) return false;
  const ts = typeof timestampSec === "string" ? parseInt(timestampSec, 10) : timestampSec;
  if (isNaN(ts)) return false;

  const nowSec = Math.floor(Date.now() / 1000);
  return Math.abs(nowSec - ts) <= maxToleranceSec;
}

/**
 * Tabela de Idempotência: Checa se o evento já foi processado e registra atomicamente.
 * Previne crédito ou mutação dupla em caso de retries do gateway ou ataques de repetição.
 */
export async function recordWebhookEvent(
  gateway: string,
  eventId: string,
  eventType: string,
  payload?: Record<string, unknown>
): Promise<{ isDuplicate: boolean; error?: string }> {
  try {
    const admin = createAdminClient();

    // 1. Checa existência prévia
    const { data: existing, error: checkError } = await admin
      .from("processed_webhook_events")
      .select("id")
      .eq("gateway", gateway)
      .eq("event_id", eventId)
      .maybeSingle();

    if (checkError) {
      return { isDuplicate: false, error: checkError.message };
    }

    if (existing) {
      return { isDuplicate: true };
    }

    // 2. Insere na tabela de idempotência
    const { error: insertError } = await admin
      .from("processed_webhook_events")
      .insert({
        gateway,
        event_id: eventId,
        event_type: eventType,
        status: "success",
        payload: payload || {},
      });

    if (insertError) {
      // 23505 = unique_violation no PostgreSQL
      if (insertError.code === "23505") {
        return { isDuplicate: true };
      }
      return { isDuplicate: false, error: insertError.message };
    }

    return { isDuplicate: false };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Erro desconhecido na verificação de idempotência.";
    return { isDuplicate: false, error: message };
  }
}
