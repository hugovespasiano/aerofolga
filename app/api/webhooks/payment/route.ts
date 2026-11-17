import { NextRequest, NextResponse } from "next/server";
import { updateUserPlan, verifyWebhookSecret } from "@/lib/payments/service";
import type { PaymentWebhookPayload, Plan } from "@/types/payments";

export async function POST(request: NextRequest) {
  try {
    // 1. Verificação de Autenticidade do Webhook
    const authHeader =
      request.headers.get("x-webhook-secret") ||
      request.headers.get("authorization")?.replace("Bearer ", "");

    if (!verifyWebhookSecret(authHeader || null)) {
      return NextResponse.json(
        { error: "Acesso negado: Secret de webhook inválido ou ausente." },
        { status: 401 }
      );
    }

    // 2. Extração e validação do payload
    const body: PaymentWebhookPayload = await request.json();

    if (!body.userId || !body.plan) {
      return NextResponse.json(
        { error: "Payload inválido: userId e plan são obrigatórios." },
        { status: 400 }
      );
    }

    const validPlans: Plan[] = ["free", "premium"];
    if (!validPlans.includes(body.plan)) {
      return NextResponse.json(
        { error: `Plano inválido: deve ser ${validPlans.join(" ou ")}.` },
        { status: 400 }
      );
    }

    // 3. Execução da promoção/rebaixamento de plano
    const result = await updateUserPlan(body.userId, body.plan, {
      provider: body.provider || "manual",
      event: body.event,
      customerId: body.customerId,
      subscriptionId: body.subscriptionId,
      ...body.metadata,
    });

    if (!result.success) {
      return NextResponse.json({ error: result.error }, { status: 500 });
    }

    return NextResponse.json(
      {
        received: true,
        userId: body.userId,
        previousPlan: result.previousPlan,
        newPlan: result.newPlan,
      },
      { status: 200 }
    );
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Erro interno no processamento do webhook.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
