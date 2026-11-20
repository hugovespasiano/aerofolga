import { NextRequest, NextResponse } from "next/server";
import {
  updateUserPlan,
  verifyWebhookSecret,
  verifyWebhookHmacSignature,
  isTimestampValid,
  recordWebhookEvent,
} from "@/lib/payments/service";
import type { PaymentWebhookPayload, Plan } from "@/types/payments";

export async function POST(request: NextRequest) {
  try {
    // 0. Fail-Closed: Segredo obrigatório no ambiente do servidor
    if (!process.env.PAYMENT_WEBHOOK_SECRET) {
      console.error("ERRO CRÍTICO: PAYMENT_WEBHOOK_SECRET não configurada no servidor.");
      return NextResponse.json(
        { error: "Configuração interna do webhook pendente." },
        { status: 500 }
      );
    }

    // 1. Extração do corpo bruto (Raw Body) para validação matemática de hash
    const rawBody = await request.text();
    if (!rawBody) {
      return NextResponse.json(
        { error: "Corpo da requisição vazio." },
        { status: 400 }
      );
    }

    // 2. Validação Criptográfica e Autenticação (HMAC-SHA256 ou Segredo Timing-Safe)
    const signature =
      request.headers.get("x-signature") ||
      request.headers.get("stripe-signature") ||
      request.headers.get("x-hub-signature-256");

    const authHeader =
      request.headers.get("x-webhook-secret") ||
      request.headers.get("authorization")?.replace("Bearer ", "");

    let isAuthenticated = false;

    if (signature) {
      isAuthenticated = verifyWebhookHmacSignature(rawBody, signature);
    } else if (authHeader) {
      isAuthenticated = verifyWebhookSecret(authHeader);
    }

    if (!isAuthenticated) {
      return NextResponse.json(
        { error: "Acesso negado: Assinatura HMAC ou segredo de webhook inválido." },
        { status: 401 }
      );
    }

    // 3. Prevenção Contra Replay Attacks (Janela Temporal Máxima de 5 Minutos)
    const timestampHeader =
      request.headers.get("x-webhook-timestamp") ||
      request.headers.get("stripe-signature")?.match(/t=(\d+)/)?.[1];

    if (timestampHeader && !isTimestampValid(timestampHeader, 300)) {
      return NextResponse.json(
        { error: "Acesso negado: Notificação expirada (possível ataque de repetição)." },
        { status: 401 }
      );
    }

    // 4. Parsing e Validação Estrutural do Payload
    let body: PaymentWebhookPayload;
    try {
      body = JSON.parse(rawBody);
    } catch {
      return NextResponse.json(
        { error: "Payload malformado: JSON inválido." },
        { status: 400 }
      );
    }

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

    const gateway = body.provider || "manual";
    const eventId =
      body.eventId ||
      body.id ||
      request.headers.get("x-event-id") ||
      `${gateway}_${body.userId}_${Date.now()}`;

    // 5. Idempotência Mandatória (Anti-Crédito / Mutação Dupla)
    const idempotency = await recordWebhookEvent(
      gateway,
      eventId,
      body.event || "plan.mutation",
      body as unknown as Record<string, unknown>
    );
    if (idempotency.isDuplicate) {
      return NextResponse.json(
        {
          received: true,
          duplicate: true,
          message: "Evento já processado anteriormente (idempotência garantida).",
        },
        { status: 200 }
      );
    }

    // 6. Execução Segura da Mutação de Plano
    const result = await updateUserPlan(body.userId, body.plan, {
      provider: gateway,
      event: body.event,
      customerId: body.customerId,
      subscriptionId: body.subscriptionId,
      eventId,
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
        eventId,
      },
      { status: 200 }
    );
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Erro interno no processamento do webhook.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
