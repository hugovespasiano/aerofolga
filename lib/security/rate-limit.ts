/**
 * lib/security/rate-limit.ts — Vespasiano Labs / AeroFolga
 * Rate Limiter simples em memória com janela deslizante para mitigação de força bruta.
 * Diretriz 1 da skill web-application-security.
 */

interface RateLimitRecord {
  count: number;
  resetAt: number;
}

const rateLimitStore = new Map<string, RateLimitRecord>();

/**
 * Limpa periodicamente chaves expiradas para evitar vazamento de memória.
 */
setInterval(() => {
  const now = Date.now();
  for (const [key, record] of rateLimitStore.entries()) {
    if (now > record.resetAt) {
      rateLimitStore.delete(key);
    }
  }
}, 60000);

export interface RateLimitResult {
  success: boolean;
  remaining: number;
  resetInSeconds: number;
}

/**
 * Verifica se a chave excedeu o limite de requisições na janela.
 * @param key Identificador único (ex: IP ou IP + email)
 * @param maxRequests Número máximo de requisições permitidas
 * @param windowSeconds Tamanho da janela em segundos (padrão: 900s = 15min)
 */
export function checkRateLimit(
  key: string,
  maxRequests: number = 5,
  windowSeconds: number = 900
): RateLimitResult {
  const now = Date.now();
  const windowMs = windowSeconds * 1000;
  const record = rateLimitStore.get(key);

  if (!record || now > record.resetAt) {
    rateLimitStore.set(key, {
      count: 1,
      resetAt: now + windowMs,
    });
    return {
      success: true,
      remaining: maxRequests - 1,
      resetInSeconds: windowSeconds,
    };
  }

  if (record.count >= maxRequests) {
    return {
      success: false,
      remaining: 0,
      resetInSeconds: Math.ceil((record.resetAt - now) / 1000),
    };
  }

  record.count += 1;
  return {
    success: true,
    remaining: maxRequests - record.count,
    resetInSeconds: Math.ceil((record.resetAt - now) / 1000),
  };
}
