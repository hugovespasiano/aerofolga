/**
 * lib/security/turnstile.ts — Vespasiano Labs / AeroFolga
 * Validação de token Cloudflare Turnstile no servidor (siteverify).
 * Opera estritamente em modo FAIL-CLOSED conforme Diretriz 5 da skill web-application-security.
 */
export async function validateTurnstileToken(
  token: string | null | undefined,
  clientIp?: string
): Promise<boolean> {
  if (!token) {
    return false;
  }

  const secretKey = process.env.CLOUDFLARE_TURNSTILE_SECRET_KEY;
  if (!secretKey) {
    console.error(
      "ALERTA DE SEGURANÇA: CLOUDFLARE_TURNSTILE_SECRET_KEY não configurada no servidor."
    );
    return false; // Fail-closed
  }

  try {
    const formData = new URLSearchParams();
    formData.append("secret", secretKey);
    formData.append("response", token);
    if (clientIp) {
      formData.append("remoteip", clientIp);
    }

    const res = await fetch(
      "https://challenges.cloudflare.com/turnstile/v0/siteverify",
      {
        method: "POST",
        body: formData,
      }
    );

    const outcome = await res.json();
    return outcome.success === true;
  } catch (err) {
    console.error("Erro na validação do Turnstile siteverify:", err);
    return false;
  }
}
