# 🏗️ Arquitetura Técnica — AeroFolga
## Versão 2.0 — Chassi FOUNDATION-NEXT & Boring Technology

> **Especificação de Engenharia e Boring Technology para o motor de cruzamento de calendários e radar passivo de voos.**  
> *Padrão Constitucional: `hugovespasiano/meu-template-base` e `hugovespasiano/FOUNDATION-NEXT`*

---

## 🏛️ 1. Princípios de Arquitetura

1. **Boring Technology is Good Technology:**
   - Next.js (App Router canônico e estável)
   - TypeScript strict com tipagem ponta a ponta
   - Tailwind CSS + Radix UI / shadcn/ui
   - Supabase (PostgreSQL relacional com Row Level Security obrigatória)
   - BrasilAPI (conector público sem custo para feriados nacionais)
2. **Context over Prompt Engineering:**
   - As regras de negócio (interseção de folgas e auditoria de tarifas) são resolvidas por algoritmos determinísticos em código TypeScript (`lib/engine/intersection.ts`).
   - A IA atua na ingestão e interpretação semântica de Decretos de Diários Oficiais e na curadoria das mensagens de notificação.
3. **Backend-First & Segurança Constitucional:**
   - Frontend controla navegação e experiência (UX).
   - Backend, rotas autenticadas e RLS no banco controlam autorização e escopo multi-tenant do casal.

---

## 🧱 2. Estrutura de Pastas do Repositório

```text
aerofolga/
├── README.md               # Manifesto do produto, 8 Pilares do Tilli e ANAC Res 400
├── AGENTS.md               # Protocolo operacional do Arquiteto Guardião (v8.3.0)
├── SECURITY_AGENT.md       # Protocolo operacional do Auditor de Segurança (Agente 02)
├── .env.example            # Variáveis tipadas para Supabase, Notificações e APIs
├── docs/                   # Documentação técnica e relatórios de auditoria
│   └── ARCHITECTURE.md     # Este documento
├── app/                    # Next.js App Router
│   ├── layout.tsx          # Root Layout com Geist e ThemeProvider
│   ├── page.tsx            # Dashboard interativo do casal
│   ├── auth/               # Fluxos de autenticação Supabase SSR
│   └── api/                # Endpoints e Webhooks
├── components/             # Componentes de UI
│   ├── aerofolga/          # CoupleDashboard e painéis do radar de voos
│   └── ui/                 # Primitivas shadcn / Radix UI
├── lib/                    # Lógica de negócio e conectores
│   ├── api/brasilapi.ts    # Conector de feriados nacionais e estaduais
│   ├── data/               # Tabela canônica de cidades do Sul Fluminense
│   ├── engine/             # Motor determinístico de interseção e radar
│   └── supabase/           # Clientes SSR, Server e Admin do Supabase
└── supabase/
    └── migrations/         # Migrações SQL versionadas com RLS estrita
```

---

## 🧩 3. Módulos do Sistema

### 3.1. `Calendar Intersection Engine` (`lib/engine/intersection.ts`)
* **Entradas:**
  - Usuário 1: Cidade de lotação (ex: Resende / Itatiaia / Volta Redonda), cargo e saldo de folgas do TRE.
  - Usuário 2: Cidade de lotação do parceiro(a) e saldo de banco de horas.
  - Tabela canônica de feriados municipais (`cities_canonical` e `municipal_holidays`).
  - BrasilAPI: Feriados nacionais e estaduais com revalidação a cada 24 horas.
* **Saída:** Janelas contínuas de 3 a 5 dias de folga simultânea (quarta a domingo, sexta a terça ou emendas de feriados).

### 3.2. `Flight Deal Engine` (Radar dos 8 Pilares do Tilli)
* **Origens Homologadas para o Sul Fluminense:**
  - Galeão (GIG) e Santos Dumont (SDU) — Rio de Janeiro.
  - Guarulhos (GRU), Congonhas (CGH) e Viracopos (VCP) — São Paulo.
  - Zona da Mata / Juiz de Fora (IZA) — Minas Gerais.
* **Auditorias Obrigatórias:**
  - Conexões humanas: tempo máximo de escala de 3 a 4 horas em território nacional.
  - Proibição estrita de troca física de aeroportos (ex: pousar em CGH e ter que ir para GRU).
  - Auditoria de taxas ocultas e bagagens.
  - Blindagem da Resolução 400 da ANAC (proteção jurídica em bilhetes de ida e volta).
  - Gatilho de alerta: Tarifa no mínimo 40% abaixo do preço médio histórico.

### 3.3. `Notification Engine` (Alertas Passivos)
* Disparo automatizado no canal preferido do casal (Telegram Bot ou WhatsApp API).
* O usuário não faz buscas ativas; recebe o alerta formatado com a economia líquida e link direto de emissão.
