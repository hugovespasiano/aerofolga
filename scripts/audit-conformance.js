#!/usr/bin/env node
/**
 * scripts/audit-conformance.js — Vespasiano Labs
 * Validador Automatizado de Conformidade do Contrato da Fundação (FOUNDATION_CONTRACT.md)
 * Executável via: npm run audit:conformance
 * Zero dependências externas (100% Node.js nativo).
 */

const fs = require("fs");
const path = require("path");

const ROOT_DIR = process.cwd();

// Cores ANSI para saída no terminal
const RESET = "\x1b[0m";
const BOLD = "\x1b[1m";
const GREEN = "\x1b[32m";
const RED = "\x1b[31m";
const YELLOW = "\x1b[33m";
const CYAN = "\x1b[36m";

console.log(`\n${BOLD}${CYAN}========================================================================${RESET}`);
console.log(`${BOLD}${CYAN}  VESPASIANO LABS — LINTER DE CONFORMIDADE ARQUITETURAL DA FUNDAÇÃO    ${RESET}`);
console.log(`${BOLD}${CYAN}  Auditando conformidade com: FOUNDATION_CONTRACT.md                   ${RESET}`);
console.log(`${BOLD}${CYAN}========================================================================${RESET}\n`);

const results = [];

function recordCheck(id, name, passed, details) {
  results.push({ id, name, passed, details });
  const icon = passed ? `${GREEN}✔ PASSOU${RESET}` : `${RED}✖ FALHOU${RESET}`;
  console.log(`  [${id}] ${icon} — ${BOLD}${name}${RESET}`);
  if (!passed && details) {
    console.log(`      ${RED}Motivo: ${details}${RESET}`);
  }
}

function readFileSafe(filePath) {
  try {
    const fullPath = path.resolve(ROOT_DIR, filePath);
    if (!fs.existsSync(fullPath)) return null;
    return fs.readFileSync(fullPath, "utf-8");
  } catch {
    return null;
  }
}

function getAllFiles(dirPath, extension) {
  let fileList = [];
  try {
    const fullDir = path.resolve(ROOT_DIR, dirPath);
    if (!fs.existsSync(fullDir)) return [];
    const entries = fs.readdirSync(fullDir, { withFileTypes: true });
    for (const entry of entries) {
      const res = path.join(dirPath, entry.name);
      if (entry.isDirectory()) {
        fileList = fileList.concat(getAllFiles(res, extension));
      } else if (!extension || entry.name.endsWith(extension)) {
        fileList.push(res);
      }
    }
  } catch {
    // Ignore errors
  }
  return fileList;
}

// -----------------------------------------------------------------------------
// CHECK 01: .gitignore Whitelist Restrita
// -----------------------------------------------------------------------------
const gitignore = readFileSafe(".gitignore");
if (!gitignore) {
  recordCheck("01", ".gitignore com Whitelist Restrita", false, "Arquivo .gitignore ausente.");
} else {
  const hasEnvWildcard = /\.env(\.\*|\*)/i.test(gitignore);
  const hasExampleException = gitignore.includes("!.env.example");
  const hasKeyBlock = gitignore.includes("*.key") || gitignore.includes("secrets/");
  if (hasEnvWildcard && hasExampleException && hasKeyBlock) {
    recordCheck("01", ".gitignore com Whitelist Restrita", true);
  } else {
    recordCheck("01", ".gitignore com Whitelist Restrita", false, "Não bloqueia .env.* ou não preserva !.env.example.");
  }
}

// -----------------------------------------------------------------------------
// Carregar todas as migrations SQL
// -----------------------------------------------------------------------------
const sqlFiles = getAllFiles("supabase/migrations", ".sql");
let allSql = "";
sqlFiles.forEach((file) => {
  const content = readFileSafe(file);
  if (content) allSql += `\n-- File: ${file}\n` + content;
});

// -----------------------------------------------------------------------------
// CHECK 02: public.profiles + Trigger Idempotente (Anti-Race Condition)
// -----------------------------------------------------------------------------
if (!allSql) {
  recordCheck("02", "Substrato Universal de Identidade (public.profiles + Idempotência)", false, "Nenhuma migration encontrada em supabase/migrations.");
} else {
  const hasProfilesTable = /CREATE\s+TABLE[^(]+public\.profiles/i.test(allSql) || /CREATE\s+TABLE[^(]+profiles/i.test(allSql);
  const hasProfilesRls = /ALTER\s+TABLE[^(]+profiles\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY/i.test(allSql);
  const hasUserTrigger = /CREATE\s+TRIGGER\s+on_auth_user_created/i.test(allSql) || /handle_new_user/i.test(allSql);
  
  // Audita especificamente se a trigger de novos usuários possui cláusula de idempotência (Anti-Race Condition)
  const handleNewUserBlock = allSql.match(/FUNCTION\s+(public\.)?handle_new_user[\s\S]*?END;/i);
  const hasIdempotentTrigger = handleNewUserBlock ? /ON\s+CONFLICT/i.test(handleNewUserBlock[0]) : /ON\s+CONFLICT\s*(\(\s*id\s*\))?\s+DO\s+(NOTHING|UPDATE)/i.test(allSql);

  if (hasProfilesTable && hasProfilesRls && hasUserTrigger && hasIdempotentTrigger) {
    recordCheck("02", "Substrato Universal de Identidade (public.profiles + Idempotência ON CONFLICT)", true);
  } else {
    let missing = [];
    if (!hasProfilesTable) missing.push("tabela profiles");
    if (!hasProfilesRls) missing.push("RLS em profiles");
    if (!hasUserTrigger) missing.push("trigger on_auth_user_created");
    if (!hasIdempotentTrigger) missing.push("idempotência ON CONFLICT (id) DO NOTHING");
    recordCheck(
      "02",
      "Substrato Universal de Identidade (public.profiles + Idempotência ON CONFLICT)",
      false,
      `Requisitos de identidade pendentes: ${missing.join(", ")}.`
    );
  }
}

// -----------------------------------------------------------------------------
// CHECK 03: public.audit_logs (Caixa Preta de Auditoria)
// -----------------------------------------------------------------------------
const hasAuditTable = /CREATE\s+TABLE[^(]+public\.audit_logs/i.test(allSql) || /CREATE\s+TABLE[^(]+audit_logs/i.test(allSql);
const hasAuditRls = /ALTER\s+TABLE[^(]+audit_logs\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY/i.test(allSql);

if (hasAuditTable && hasAuditRls) {
  recordCheck("03", "Trilha Imutável de Auditoria (public.audit_logs)", true);
} else {
  recordCheck("03", "Trilha Imutável de Auditoria (public.audit_logs)", false, "Tabela audit_logs ou RLS ausente no schema.");
}

// -----------------------------------------------------------------------------
// CHECK 04: public.processed_webhook_events (Tabela de Idempotência)
// -----------------------------------------------------------------------------
const hasIdempotencyTable = /CREATE\s+TABLE[^(]+public\.processed_webhook_events/i.test(allSql) || /CREATE\s+TABLE[^(]+processed_webhook_events/i.test(allSql);
const hasUniqueConstraint = /CONSTRAINT\s+\w+\s+UNIQUE\s*\(\s*gateway\s*,\s*event_id\s*\)/i.test(allSql) || /UNIQUE\s*\(\s*gateway\s*,\s*event_id\s*\)/i.test(allSql);

if (hasIdempotencyTable && hasUniqueConstraint) {
  recordCheck("04", "Tabela de Idempotência Persistida (processed_webhook_events)", true);
} else {
  recordCheck("04", "Tabela de Idempotência Persistida (processed_webhook_events)", false, "Tabela processed_webhook_events ou chave única (gateway, event_id) ausente.");
}

// -----------------------------------------------------------------------------
// CHECK 05: Webhook com HMAC-SHA256 e Comparação Timing-Safe
// -----------------------------------------------------------------------------
const webhookRoute = readFileSafe("app/api/webhooks/payment/route.ts");
const paymentService = readFileSafe("lib/payments/service.ts");

if (!webhookRoute && !paymentService) {
  recordCheck("05", "Webhook com Validação Criptográfica HMAC-SHA256", true, "Nenhuma rota de webhook detectada (N/A).");
} else {
  const hasHmac = paymentService && /createHmac/i.test(paymentService);
  const hasTimingSafe = paymentService && /timingSafeEqual/i.test(paymentService);
  const hasRawBody = webhookRoute && /request\.text\(\)/i.test(webhookRoute);

  if (hasHmac && hasTimingSafe && hasRawBody) {
    recordCheck("05", "Webhook com Validação Criptográfica HMAC-SHA256", true);
  } else {
    recordCheck(
      "05",
      "Webhook com Validação Criptográfica HMAC-SHA256",
      false,
      `Exige captura de rawBody, crypto.createHmac e crypto.timingSafeEqual (Raw: ${!!hasRawBody}, HMAC: ${!!hasHmac}, TimingSafe: ${!!hasTimingSafe}).`
    );
  }
}

// -----------------------------------------------------------------------------
// CHECK 06: Prevenção Anti-Replay Temporal em Webhooks (300s)
// -----------------------------------------------------------------------------
if (!webhookRoute && !paymentService) {
  recordCheck("06", "Prevenção Anti-Replay Temporal em Webhooks (300s)", true, "N/A.");
} else {
  const hasAntiReplay =
    (paymentService && /isTimestampValid/i.test(paymentService)) ||
    (webhookRoute && /timestamp/i.test(webhookRoute) && /300/i.test(webhookRoute));

  if (hasAntiReplay) {
    recordCheck("06", "Prevenção Anti-Replay Temporal em Webhooks (300s)", true);
  } else {
    recordCheck("06", "Prevenção Anti-Replay Temporal em Webhooks (300s)", false, "Ausência de verificação de timestamp ou janela temporal de 300 segundos.");
  }
}

// -----------------------------------------------------------------------------
// CHECK 07: Trava de Idempotência Ativa no Handler do Webhook
// -----------------------------------------------------------------------------
if (!webhookRoute) {
  recordCheck("07", "Deduplicação de Eventos Ativa no Webhook", true, "N/A.");
} else {
  const hasIdempotencyCall = /recordWebhookEvent/i.test(webhookRoute) && /duplicate/i.test(webhookRoute);
  if (hasIdempotencyCall) {
    recordCheck("07", "Deduplicação de Eventos Ativa no Webhook", true);
  } else {
    recordCheck("07", "Deduplicação de Eventos Ativa no Webhook", false, "O handler não consulta nem registra o evento antes de mutar o plano.");
  }
}

// -----------------------------------------------------------------------------
// CHECK 08: Interceptor de Borda (proxy.ts ou middleware.ts)
// -----------------------------------------------------------------------------
const proxyFile = readFileSafe("proxy.ts") || readFileSafe("middleware.ts");
const supabaseProxy = readFileSafe("lib/supabase/proxy.ts");

if (!proxyFile) {
  recordCheck("08", "Interceptor de Borda (proxy.ts ou middleware.ts)", false, "Nenhum arquivo proxy.ts ou middleware.ts encontrado na raiz.");
} else {
  const callsUpdateSession = /updateSession/i.test(proxyFile);
  const isEdgeSafe = supabaseProxy && !/import\s+.*cookies.*from\s+["']next\/headers["']/i.test(supabaseProxy);

  if (callsUpdateSession && isEdgeSafe) {
    recordCheck("08", "Interceptor de Borda (proxy.ts / Edge-Safe)", true);
  } else {
    recordCheck(
      "08",
      "Interceptor de Borda (proxy.ts / Edge-Safe)",
      false,
      `proxy.ts não chama updateSession ou importa next/headers quebrando o Edge Runtime (UpdateSession: ${callsUpdateSession}, EdgeSafe: ${isEdgeSafe}).`
    );
  }
}

// -----------------------------------------------------------------------------
// CHECK 09: Matriz dos 6 Security Headers Canônicos em next.config
// -----------------------------------------------------------------------------
const nextConfig = readFileSafe("next.config.ts") || readFileSafe("next.config.js") || readFileSafe("next.config.mjs");
if (!nextConfig) {
  recordCheck("09", "Matriz dos 6 Security Headers Canônicos (CSP, HSTS)", false, "Arquivo next.config ausente.");
} else {
  const hasHeadersFn = /headers\s*\(\s*\)/i.test(nextConfig);
  const hasCsp = /Content-Security-Policy/i.test(nextConfig);
  const hasXFrame = /X-Frame-Options/i.test(nextConfig);
  const hasNosniff = /X-Content-Type-Options/i.test(nextConfig);
  const hasHsts = /Strict-Transport-Security/i.test(nextConfig);
  const hasReferrer = /Referrer-Policy/i.test(nextConfig);
  const hasPermissions = /Permissions-Policy/i.test(nextConfig);

  const allHeadersPresent = hasHeadersFn && hasCsp && hasXFrame && hasNosniff && hasHsts && hasReferrer && hasPermissions;

  if (allHeadersPresent) {
    recordCheck("09", "Matriz dos 6 Security Headers Canônicos (CSP, HSTS, X-Frame)", true);
  } else {
    recordCheck(
      "09",
      "Matriz dos 6 Security Headers Canônicos (CSP, HSTS, X-Frame)",
      false,
      "Faltam cabeçalhos de segurança obrigatórios em next.config (headers(), CSP, X-Frame, nosniff, HSTS, Referrer, Permissions)."
    );
  }
}

// -----------------------------------------------------------------------------
// CHECK 10: Módulos Anti-Robô (Turnstile) e Rate Limiting
// -----------------------------------------------------------------------------
const turnstileHelper = readFileSafe("lib/security/turnstile.ts");
const rateLimitHelper = readFileSafe("lib/security/rate-limit.ts");

const hasTurnstile = turnstileHelper && /challenges\.cloudflare\.com\/turnstile\/v0\/siteverify/i.test(turnstileHelper);
const hasRateLimit = rateLimitHelper && /checkRateLimit/i.test(rateLimitHelper);

if (hasTurnstile && hasRateLimit) {
  recordCheck("10", "Helpers de Proteção Anti-Robô (Turnstile) e Rate Limiting", true);
} else {
  recordCheck(
    "10",
    "Helpers de Proteção Anti-Robô (Turnstile) e Rate Limiting",
    false,
    `Módulos ausentes em lib/security (Turnstile: ${!!hasTurnstile}, RateLimit: ${!!hasRateLimit}).`
  );
}

// -----------------------------------------------------------------------------
// Resumo Final e Código de Saída
// -----------------------------------------------------------------------------
console.log(`\n${BOLD}${CYAN}------------------------------------------------------------------------${RESET}`);
const totalPassed = results.filter((r) => r.passed).length;
const totalFailed = results.length - totalPassed;

if (totalFailed === 0) {
  console.log(`${BOLD}${GREEN}  🎉 PARABÉNS! ${totalPassed}/${results.length} CHECKS APROVADOS!${RESET}`);
  console.log(`${GREEN}  A aplicação cumpre 100% do Contrato Arquitetural da Fundação (Vespasiano Labs).${RESET}`);
  console.log(`${BOLD}${CYAN}========================================================================${RESET}\n`);
  process.exit(0);
} else {
  console.log(`${BOLD}${RED}  ❌ REPROVADO: ${totalFailed} de ${results.length} requisitos foram violados.${RESET}`);
  console.log(`${RED}  Consulte docs/FOUNDATION_CONTRACT.md para implementar as correções antes do deploy.${RESET}`);
  console.log(`${BOLD}${CYAN}========================================================================${RESET}\n`);
  process.exit(1);
}
