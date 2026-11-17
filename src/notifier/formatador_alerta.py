"""
formatador_alerta.py — AeroFolga / Vespasiano Labs
Formatação persuasiva e humanizada da notificação de viagem para o casal,
incluindo o Parecer Logístico "Porta a Porta" saindo de Volta Redonda.
"""

from calendar_engine.calculadora_janelas import JanelaViagem
from flight_engine.filtros_tilli import PropostaVoo
from decision_engine.custo_porta_a_porta import calcular_logistica


def formatar_alerta_whatsapp(janela: JanelaViagem, voo: PropostaVoo) -> str:
    """
    Formata a mensagem exatamente no padrão de alta conversão do WhatsApp.
    """
    alavancagem_texto = ""
    if janela.custo_tre > 0:
        alavancagem_texto = f"\n💡 *Estratégia:* Utilizada {janela.custo_tre} folga do TRE para conectar a viagem!"

    # Cálculo do Custo Real Porta a Porta
    log = calcular_logistica(voo.origem)
    passagens_casal = voo.preco_brl * 2
    custo_final_casal = passagens_casal + log.custo_logistico_total

    if voo.origem in ("GIG", "SDU"):
        selo_logistica = "🟢 ESCOLHA INTELIGENTE (Saída Rápida via Rio)"
        detalhe_transporte = f"• Cidade do Aço (VR ⇄ Novo Rio) + Uber: R$ {log.custo_logistico_total:.2f} (sem pernoite)"
    else:
        selo_logistica = "⚠️ ATENÇÃO: Saída por São Paulo"
        detalhe_transporte = (
            f"• Cometa (VR ⇄ Tietê) + Uber + Diária Airbnb/Hotel: R$ {log.custo_logistico_total:.2f}\n"
            f"• Desgaste: {log.horas_estrada_total}h de estrada na Dutra"
        )

    return f"""✈️ *[AeroFolga] Janela de Viagem em Casal Detectada!*

📅 *Período:* {janela.to_dict()['periodo']} ({janela.dias_totais} dias livres)
• *Tipo:* {janela.tipo}{alavancagem_texto}

🛫 *Voo:* {voo.origem} ⇄ {voo.destino}
• *Companhia:* {voo.companhia} (Voo Direto)
• *Tarifa Aérea:* *R$ {voo.preco_brl:.2f}* por pessoa (R$ {passagens_casal:.2f} casal)
• *Economia Voo:* *{voo.desconto_percentual}% OFF* (Média histórica: R$ {voo.preco_historico_brl:.2f})
• *Bagagem:* Mala de mão de 10kg inclusa

🚗 *Análise Porta a Porta (Saindo de Volta Redonda):*
• *Status:* {selo_logistica}
{detalhe_transporte}
• *CUSTO FINAL REAL DO CASAL:* *R$ {custo_final_casal:.2f}* (Passagens + Deslocamento)

🔗 *Link Direto no Google Flights:*
{voo.url_reserva}

---
_AeroFolga — Vespasiano Labs | Inteligência Passiva de Viagens_"""
