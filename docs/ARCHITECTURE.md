# 🏗️ Arquitetura Técnica — AeroFolga

> **Especificação de Engenharia e Boring Technology para o motor de cruzamento de calendários e radar de voos.**  
> *Padrão Constitucional: `hugovespasiano/meu-template-base`*

---

## 🏛️ 1. Princípios de Arquitetura

1. **Boring Technology:** Banco de dados SQLite/PostgreSQL simples, scripts Python leves, filas assíncronas via cronjobs/workers sem complexidade excessiva de microsserviços.
2. **Context over Prompt Engineering:** As regras de negócio (interseção de datas e filtros de voo) são resolvidas por algoritmos determinísticos em código. A IA entra apenas para interpretação de Diários Oficiais e geração da mensagem contextualizada no WhatsApp.
3. **Privacidade e Soberania:** Dados dos calendários locais não são vazados para terceiros.

---

## 🧱 2. Estrutura de Pastas do Repositório

```text
aerofolga/
├── README.md               # Manifesto do produto e visão comercial
├── docs/                   # Especificações de arquitetura e API
│   └── ARCHITECTURE.md     # Este documento
├── data/                   # Exemplos e esquemas de dados
│   ├── calendarios/        # Arquivos de calendário dos usuários
│   └── destinos.json       # Rotas de interesse e preços médios históricos
└── src/                    # Código-fonte do motor
    ├── calendar_engine/    # Motor de ingestão e interseção de folgas
    ├── flight_engine/      # Scraper/API e aplicação dos 4 pilares do Tilli
    └── notifier/           # Disparador de mensagens no WhatsApp/Telegram
```

---

## 🧩 3. Módulos do Sistema

### 3.1. `calendar_engine` (Motor de Interseção de Calendários)
* **Entradas:**
  - Calendário do Usuário 1 (Hugo: Itatiaia, SEEDUC-RJ, Folgas TRE).
  - Calendário do Usuário 2 (Esposa: Prefeitura de Volta Redonda).
  - Leitor de Diários Oficiais (pontos facultativos decretados).
* **Saída:** Lista de janelas de oportunidade em formato ISO:
  ```json
  [
    {
      "inicio": "2026-05-14",
      "fim": "2026-05-18",
      "total_dias": 5,
      "tipo_janela": "quarta_a_domingo",
      "motivos": [
        "Hugo: Folga TRE (2 dias) + Feriado Municipal",
        "Esposa: Ponto Facultativo Volta Redonda"
      ]
    }
  ]
  ```

### 3.2. `flight_engine` (Motor de Radar de Passagens)
* **Origens Homologadas (Sul Fluminense):**
  - Galeão (GIG) e Santos Dumont (SDU) — Rio de Janeiro.
  - Guarulhos (GRU), Congonhas (CGH) e Viracopos (VCP) — São Paulo.
  - Zona da Mata / Juiz de Fora (IZA) — Minas Gerais.
* **Filtros dos 4 Pilares (Tilli):**
  - Voo direto ou conexão máxima de 3 horas.
  - Proibição estrita de troca física de aeroporto.
  - Verificação de taxa de bagagem inclusa.
  - Gatilho de alerta: Preço da janela $\le 0.60 \times \text{Preço Médio Histórico}$ (desconto mínimo de 40%).

### 3.3. `notifier` (Motor de Alerta)
* Integração direta com a API do WhatsApp Business (Meta Oficial) ou bot do Telegram.
* Formatação humanizada com resumo da economia líquida e link direto de compra.
