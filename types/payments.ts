import type { Plan } from "@/types/access";

export type { Plan };

export type PaymentProvider = "stripe" | "mercadopago" | "kiwify" | "asaas" | "manual";

export type PaymentEventType =
  | "payment.succeeded"
  | "payment.failed"
  | "subscription.created"
  | "subscription.updated"
  | "subscription.canceled";

export interface PaymentWebhookPayload {
  event: PaymentEventType;
  userId: string;
  plan: Plan;
  provider: PaymentProvider;
  customerId?: string;
  subscriptionId?: string;
  metadata?: Record<string, unknown>;
}

export interface UpdatePlanResult {
  success: boolean;
  previousPlan?: Plan;
  newPlan?: Plan;
  error?: string;
}
