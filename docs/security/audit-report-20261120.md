# Relatório de Auditoria de Segurança — 2026-11-20
**Auditor:** Agente 02 (Security Auditor & Validador Cético)  
**Modalidade:** Auditoria Estática Estritamente Somente-Leitura (Static Code Analysis & Adversarial Inspection)  
**Versão de Referência:** Template Base v2.8.0 / SKILL Standards (Web App Security, AI Cost Governance, Webhook Financial Integrity)  
**Alvo Auditado:** AeroFolga (`C:\Users\hugov\.gemini\antigravity\scratch\aerofolga`)  
**Status Global:** 
[ ] Sem vulnerabilidades identificadas dentro do escopo
[ ] Ressalvas identificadas (Ajustes recomendados)
[x] Vulnerabilidade crítica identificada (Ação imediata)
[ ] Auditoria inconclusiva

---

## 1. Matriz de Cobertura da Auditoria (Coverage Ledger)

> **Regra Obrigatória:** Percentuais calculados com base na inspeção real dos componentes do projeto.

| Componente / Módulo | Arquivos / Policies Inspecionadas | Grau de Cobertura | Justificativa / Observação |
| :--- | :--- | :---: | :--- |
| **Autenticação & Sessões** | `components/login-form.tsx`, `components/sign-up-form.tsx`, `components/forgot-password-form.tsx`, `app/auth/callback/route.ts`, `app/auth/confirm/route.ts` | 100% | Roteamento inspecionado; ausência de Turnstile e rate-limit. |
| **RLS & Isolamento de Dados** | `supabase/migrations/00000000000001_aerofolga_schema.sql` (6 tabelas) | 100% | 6 tabelas com RLS habilitada; isolamento por `auth.uid() = user_id`. |
| **RPCs & SECURITY DEFINER** | Todas as migrations e queries de banco | 100% | Inspecionado: zero funções RPC customizadas declaradas. |
| **Upload & Storage** | `lib/storage/service.ts`, `lib/storage/helpers.ts` | 100% | Camada de código presente herdada do template; buckets físicos ainda não provisionados. |
| **Integridade de Banco & Soft Delete** | `supabase/migrations/00000000000001_aerofolga_schema.sql` | 100% | Foreign keys utilizam `ON DELETE CASCADE` estrito no chassi de casais. |
| **Borda & Blindagem de Origem** | `next.config.ts`, ausência de `middleware.ts` | 100% | Zero cabeçalhos injetados em `next.config.ts`; middleware ausente. |
| **Ingestão de Documentos & OCR** | `src/calendar_engine/extrator_visual.py` | 100% | Apenas template de prompt local; zero chamadas ativas ou API keys. |
| **Consumo de IA & Quotas** | Varredura em `src/`, `app/`, `lib/` | 100% | Sem SDKs ativos de OpenAI/Gemini/Anthropic disparando chamadas em produção. |
| **Webhooks & Integridade Financeira** | `app/api/webhooks/payment/route.ts`, `lib/payments/service.ts` | 100% | Inspecionado exaustivamente: ausência de HMAC, replay tolerance e idempotência. |
| **Criptografia em Repouso & Segredos** | `.env`, `.env.example`, `.gitignore`, `lib/supabase/admin.ts`, `src/notifier/disparador.py` | 100% | Segredos do Telegram isolados em `.env`; `.gitignore` incompleto para `.env.*`. |
| **Rate Limiting & Anti-Brute Force** | Rotas de autenticação e API | 100% | Inexistente em nível de Next.js e frontend. |
| **Cookies & Sessões (HttpOnly/Secure)** | `lib/supabase/server.ts`, `lib/supabase/proxy.ts`, `lib/supabase/client.ts` | 100% | SSR configurado, mas órfão sem ativação no `middleware.ts`. |
| **CORS, CSRF & Security Headers (CSP)** | `next.config.ts`, `app/layout.tsx` | 100% | Ausência dos 6 headers obrigatórios (CSP, HSTS, X-Frame-Options, etc.). |
| **Validação Turnstile no Servidor** | Todas as rotas de auth e formulários | 100% | Inexistente (zero chamadas para `challenges.cloudflare.com/turnstile/v0/siteverify`). |
| **SQL Injection em RPCs Dinâmicas** | Toda a base de código TypeScript e Python | 100% | Inspecionado: uso exclusivo de PostgREST parametrizado; zero concatenação crua. |
| **Telemetria de Incidentes & Alertas** | `app/`, `lib/`, `src/` | 100% | Ausência de Sentry ou monitoramento ativo de anomalias HTTP 401/403. |

---

## 2. Achados Confirmados (Vulnerabilidades Reais)

### 🔴 [CRÍTICA] — Rota de Webhook Financeiro Sem Validação Criptográfica HMAC-SHA256
- **Status:** `CONFIRMED`
- **Classificação:** Secrets / Auth / Financial Integrity
- **Fatores:** Impacto: Crítico | Explorabilidade: Trivial | Sensibilidade: Alta | Persistência: Alta
- **Evidência de Código:** [route.ts](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/app/api/webhooks/payment/route.ts#L8-L17) e [service.ts](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/lib/payments/service.ts#L105-L113)
- **Resultado da Contestação Cética:** A rota `POST /api/webhooks/payment` valida o chamador apenas confrontando um cabeçalho estático (`x-webhook-secret` ou `Authorization: Bearer <secret>`). Não há verificação criptográfica de assinatura (HMAC-SHA256 sobre os bytes brutos da requisição — *raw body*), contrariando o padrão de gateways sérios (Stripe, Asaas, Mercado Pago). Adicionalmente, em `lib/payments/service.ts:112`, a comparação é feita via operador `===`, expondo a aplicação a *Timing Attacks*.
- **Impacto Real:** Se o segredo estático vazar ou for adivinhado via ataque de temporização, qualquer agente externo pode forjar eventos e elevar qualquer `userId` para o plano `premium` gratuitamente.
- **Recomendação para o Guardião:** 
  1. Capturar o payload bruto como `Buffer`/texto cru.
  2. Implementar verificação criptográfica de HMAC-SHA256 utilizando `crypto.timingSafeEqual()`.
  3. Rejeitar sumariamente requisições sem assinatura válida.

---

### 🔴 [CRÍTICA] — Ausência de Tabela de Idempotência e Trava de Repetição em Webhook de Pagamento
- **Status:** `CONFIRMED`
- **Classificação:** Financial Integrity / Guard Rails
- **Fatores:** Impacto: Crítico | Explorabilidade: Trivial | Sensibilidade: Alta | Persistência: Permanente
- **Evidência de Código:** [route.ts](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/app/api/webhooks/payment/route.ts#L38-L48) e ausência de tabela em [00000000000001_aerofolga_schema.sql](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/supabase/migrations/00000000000001_aerofolga_schema.sql)
- **Resultado da Contestação Cética:** Gateways de pagamento realizam reenvios automáticos (*retries*) agressivos diante de latências. A rota atual não registra nem consulta o identificador único do evento (`event_id`). A tabela mandatória `processed_webhook_events` (exigida na skill `webhook-and-financial-integrity`) inexiste no banco de dados. Adicionalmente, não há verificação de janela temporal de tolerância (> 300s).
- **Impacto Real:** Ataques de repetição (*replay attack*) ou retries do gateway executam mutações redundantes no perfil do usuário e no fluxo transacional sem qualquer trava de concorrência ou registro de unicidade.
- **Recomendação para o Guardião:**
  1. Criar migration no Supabase com a tabela `public.processed_webhook_events` contendo `CONSTRAINT uq_gateway_event_id UNIQUE (gateway, event_id)`.
  2. Implementar checagem prévia fail-closed de tolerância temporal (máx 5 minutos) e registro atômico do `event_id` antes da mutação de plano.

---

### 🟠 [ALTA] — Desconexão Arquitetural: Tabelas de Fundação Inexistentes no Banco de Dados
- **Status:** `CONFIRMED`
- **Classificação:** Authz / Audit / Data Integrity
- **Fatores:** Impacto: Alto | Explorabilidade: Moderada | Sensibilidade: Média
- **Evidência de Código:** [service.ts](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/lib/payments/service.ts#L18-L68), [service.ts](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/lib/access/service.ts#L38-L53), [service.ts](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/lib/audit/service.ts#L18-L29) confrontados com [00000000000001_aerofolga_schema.sql](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/supabase/migrations/00000000000001_aerofolga_schema.sql#L1-L149)
- **Resultado da Contestação Cética:** Os módulos de governança herdados da Foundation (`lib/access/service.ts`, `lib/payments/service.ts`, `lib/audit/service.ts`) operam sobre as tabelas `public.profiles`, `public.audit_logs`, `public.role_permissions` e `public.permissions`. No entanto, a migration única do banco provisiona exclusivamente `couples_profiles`, `detected_windows`, `flight_deals`, `cities_canonical`, `municipal_holidays` e `official_gazette_notices`.
- **Impacto Real:** Chamadas a `getAccessProfile()`, `updateUserPlan()` e `logAuditEvent()` falham com erro PostgREST de relação inexistente (`relation does not exist`). A Caixa Preta de Auditoria está inoperante e o controle de suspensão/planos não possui persistência no banco.
- **Recomendação para o Guardião:**
  1. Decidir se o AeroFolga utilizará a tabela canônica `profiles` como âncora de identidade unificada ou sincronizará os campos `plan`, `role` e `status` diretamente em `couples_profiles`.
  2. Provisionar formalmente a tabela `public.audit_logs` e `public.processed_webhook_events` com políticas RLS restritas ao `service_role`.

---

### 🟠 [ALTA] — Ausência de `middleware.ts`: Quebra de Renovação de Sessão SSR e Bypass de Borda
- **Status:** `CONFIRMED`
- **Classificação:** Auth / Edge Protection / Session Lifecycle
- **Fatores:** Impacto: Alto | Explorabilidade: Moderada | Sensibilidade: Alta
- **Evidência de Código:** Ausência de `middleware.ts` na raiz do projeto (código órfão em [proxy.ts](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/lib/supabase/proxy.ts#L7-L65) e [server.ts](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/lib/supabase/server.ts#L26-L29))
- **Resultado da Contestação Cética:** O Next.js App Router com `@supabase/ssr` exige um arquivo `middleware.ts` na raiz para interceptar todas as requisições, invocar `updateSession()` e persistir tokens de autenticação renovados nos cookies de resposta (`Set-Cookie`). Sem o middleware, a renovação em background falha após o término da validade do JWT de curta duração. Adicionalmente, a verificação de contas suspensas em rotas protegidas (`hasAccess(profile, { requireActive: true })`) em `lib/supabase/proxy.ts` é completamente ignorada.
- **Impacto Real:** Sessões de usuários logados podem expirar abruptamente durante o uso; usuários com conta suspensa ou bloqueada conseguem atingir rotas protegidas que não implementem checagens redundantes no componente.
- **Recomendação para o Guardião:**
  1. Criar o arquivo `middleware.ts` na raiz conectando formalmente a função `updateSession(request)` de `@/lib/supabase/proxy`.
  2. Definir o `matcher` padrão para ignorar apenas assets estáticos (`_next/static`, `_next/image`, `favicon.ico`, imagens).

---

### 🟠 [ALTA] — Inexistência de Security Headers e Política de Segurança de Conteúdo (CSP)
- **Status:** `CONFIRMED`
- **Classificação:** Edge-Origin / Browser Protection
- **Fatores:** Impacto: Alto | Explorabilidade: Moderada | Sensibilidade: Média
- **Evidência de Código:** [next.config.ts](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/next.config.ts#L1-L7)
- **Resultado da Contestação Cética:** O arquivo de configuração do Next.js exporta apenas `{ cacheComponents: true }`. Não há injeção de cabeçalhos de segurança HTTP. A aplicação é servida sem:
  - `Content-Security-Policy` (delimitando origens seguras de scripts e conexões)
  - `X-Frame-Options: DENY` (deixando o portal vulnerável a sequestro de cliques — *Clickjacking* via `<iframe>`)
  - `X-Content-Type-Options: nosniff` (vulnerável a interpretação errônea de MIME types)
  - `Strict-Transport-Security` (HSTS ausente)
  - `Permissions-Policy` (deixando APIs de hardware abertas)
  - `Referrer-Policy: strict-origin-when-cross-origin`
- **Impacto Real:** A aplicação fica desprovida das defesas canônicas de navegador recomendadas pelo OWASP Top 10, facilitando ataques de Clickjacking e injeção de scripts não autorizados caso surja um vetor de XSS.
- **Recomendação para o Guardião:**
  1. Adicionar o bloco assíncrono `headers()` em `next.config.ts` injetando a matriz canônica de 6 cabeçalhos estipulada na Diretriz 4 da skill `web-application-security`.

---

### 🟠 [ALTA] — Ausência de Anti-Robô (Cloudflare Turnstile) e Rate Limiting em Rotas de Autenticação
- **Status:** `CONFIRMED`
- **Classificação:** Auth / Anti-Abuse / Brute-Force
- **Fatores:** Impacto: Alto | Explorabilidade: Trivial | Sensibilidade: Alta
- **Evidência de Código:** [login-form.tsx](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/components/login-form.tsx#L48-L67), [sign-up-form.tsx](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/components/sign-up-form.tsx#L49-L76), [forgot-password-form.tsx](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/components/forgot-password-form.tsx#L38-L59)
- **Resultado da Contestação Cética:** Os formulários disparam requisições diretas ao Supabase Auth via browser SDK sem passar por nenhum desafio de prova de humanidade (Turnstile) e sem limitador de taxa (*rate limiting*) em camada de aplicação.
- **Impacto Real:** Um invasor pode automatizar scripts para testar listas de senhas (*credential stuffing* / *brute force*), criar contas em massa e esgotar a cota de e-mails transacionais (via disparo massivo em `/auth/forgot-password`).
- **Recomendação para o Guardião:**
  1. Integrar o widget Cloudflare Turnstile no frontend nos fluxos de login, cadastro e recuperação de senha.
  2. Implementar validação mandatória no servidor via chamada `POST` para `https://challenges.cloudflare.com/turnstile/v0/siteverify` em modo *fail-closed*.
  3. Configurar teto de 5 tentativas por 15 minutos em login e 3 por hora em recuperação de senha.

---

### 🟡 [MÉDIA] — Fragilidade na Regra de `.gitignore` para Variáveis de Ambiente
- **Status:** `CONFIRMED`
- **Classificação:** Secrets & Configuration
- **Fatores:** Impacto: Médio | Explorabilidade: Trivial | Sensibilidade: Alta
- **Evidência de Código:** [.gitignore](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/.gitignore#L5-L6) confrontado com [meu-template-base/.gitignore](file:///C:/Users/hugov/.gemini/antigravity/scratch/meu-template-base/.gitignore#L1-L6)
- **Resultado da Contestação Cética:** O arquivo `.gitignore` do AeroFolga lista estritamente `.env` e `.env.local`. Arquivos como `.env.production`, `.env.staging`, `.env.development.local` ou chaves privadas (`*.pem`, `*.key`) não estão cobertos.
- **Impacto Real:** Risco real de desenvolvedores ou pipelines comitarem acidentalmente arquivos com segredos reais de produção no repositório remoto.
- **Recomendação para o Guardião:**
  1. Atualizar o bloco de segredos no `.gitignore` para o padrão do `meu-template-base`:
     ```gitignore
     .env
     .env.*
     !.env.example
     !.env.template
     *.local
     secrets/
     *.pem
     *.key
     ```

---

## 3. Achados Pendentes de Validação Ativa (`PENDING_VALIDATION`)

- **Visibilidade de Ofertas de Voo sem Janela Vinculada (`flight_deals.window_id IS NULL`):**
  - **Arquivo / Ponto de Dúvida:** [00000000000001_aerofolga_schema.sql:136-143](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/supabase/migrations/00000000000001_aerofolga_schema.sql#L136-L143)
  - **Dúvida Operacional:** A policy RLS de `flight_deals` exige um `INNER JOIN` com `detected_windows`. Se o robô de background inserir achados gerais do radar (ex: promoções relâmpago gerais não atreladas a uma janela prévia de um casal específico), esses registros não poderão ser lidos por nenhum usuário comum. É necessário alinhar com o Product Owner se ofertas gerais devem ter visualização pública/global ou se todo voo rastreado é obrigatoriamente acoplado a uma janela detectada de casal.

---

## 4. Falsos Positivos Refutados na Fase Cética (`REJECTED`)

- **Suspeita de Open Redirect nos Callbacks de Autenticação (`/auth/callback` e `/auth/confirm`):**
  - **Suspeita Inicial:** O parâmetro `?next=` poderia permitir redirecionamento arbitrário para domínios maliciosos externos.
  - **Refutação Cética Comprovada:** Inspecionando [callback/route.ts:10](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/app/auth/callback/route.ts#L10) e [confirm/route.ts:11](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/app/auth/confirm/route.ts#L11), verifica-se que ambos invocam `getSafeRedirectUrl(next)` ([utils.ts:18-24](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/lib/utils.ts#L18-L24)). A função valida estritamente URLs relativas iniciadas com `/` e rejeita qualquer tentativa de `//` ou `/\\`.
  - **Decisão:** `REJECTED` (Mitigação comprovada no código).

- **Suspeita de Exposição de `SUPABASE_SERVICE_ROLE_KEY` no Frontend:**
  - **Suspeita Inicial:** Risco de vazamento de credenciais de super-administrador no bundle do cliente.
  - **Refutação Cética Comprovada:** [admin.ts](file:///C:/Users/hugov/.gemini/antigravity/scratch/aerofolga/lib/supabase/admin.ts#L10) lê estritamente `SUPABASE_SERVICE_ROLE_KEY` e é importado exclusivamente em `lib/payments/service.ts`, que executa no servidor via route handler de webhooks. Nenhuma chave administrativa está prefixada com `NEXT_PUBLIC_` e zero referências existem em client components (`use client`).
  - **Decisão:** `REJECTED` (Isolamento de servidor comprovado).

- **Suspeita de SQL Injection em Consultas de Banco:**
  - **Suspeita Inicial:** Vulnerabilidade a injeção SQL em consultas ou RPCs dinâmicas.
  - **Refutação Cética Comprovada:** O banco de dados não possui nenhuma função `SECURITY DEFINER` com SQL dinâmico (`EXECUTE format`). Todas as consultas da aplicação utilizam o PostgREST query builder devidamente parametrizado.
  - **Decisão:** `REJECTED` (Código 100% parametrizado).

---

## 5. Checklist de Validação Manual para o Product Owner

- [ ] Validar a modelagem de identidade: confirmar se o cadastro de casais deve alimentar uma tabela canônica `profiles` para compatibilidade total com a Foundation ou se a arquitetura manterá `couples_profiles` como entidade principal.
- [ ] Definir o gateway de pagamento primário (Stripe, Asaas ou Mercado Pago) para implementação do cálculo exato de HMAC-SHA256 no webhook.
- [ ] Providenciar as chaves de Cloudflare Turnstile (`CLOUDFLARE_TURNSTILE_SITE_KEY` e `CLOUDFLARE_TURNSTILE_SECRET_KEY`) para inclusão nos formulários de autenticação.
- [ ] Confirmar a regra de negócio sobre a visibilidade de ofertas gerais de voo no radar (ofertas públicas vs acopladas a janelas de casais).

---

## 6. Parecer de Fechamento e Limitações

- **Status da Auditoria:** **Vulnerabilidade crítica identificada (Ação imediata)**
- **Limitações:** Auditoria realizada sob modo estritamente somente-leitura em nível estático de código-fonte e schema SQL. Não foram disparados ataques ativos contra instâncias de produção.
- **Decisão:** O sistema possui excelente separação de domínio para os cálculos de folgas e regras municipais, e o isolamento RLS das tabelas de casal é consistente. Contudo, a camada de **Webhooks Financeiros**, a falta de **Idempotência**, a ausência de **`middleware.ts`**, a carência de **Security Headers (CSP)** e a inexistência de **Anti-Robô (Turnstile)** no fluxo de login demandam ação imediata do **Guardião (Agente 01)** antes de qualquer publicação comercial ou abertura de tráfego público.
