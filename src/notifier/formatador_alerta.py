"""
formatador_alerta.py — AeroFolga / Vespasiano Labs
Formatação persuasiva e humanizada da notificação de viagem para o casal.
"""

from calendar_engine.calculadora_janelas import JanelaViagem
from flight_engine.filtros_tilli import PropostaVoo


def formatar_alerta_whatsapp(janela: JanelaViagem, voo: PropostaVoo) -> str:
    """
    Formata a mensagem exatamente no padrão de alta conversão do WhatsApp.
    """
    alavancagem_texto = ""
    if janela.custo_tre > 0:
        alavancagem_texto = f"\n💡 *Estratégia:* Utilizada {janela.custo_tre} folga do TRE para conectar a viagem!"

    return f"""✈️ *[AeroFolga] Janela de Viagem em Casal Detectada!*

📅 *Período:* {janela.to_dict()['periodo']} ({janela.dias_totais} dias livres)
• *Tipo:* {janela.tipo}{alavancagem_texto}

🛫 *Voo:* {voo.origem} ⇄ {voo.destino}
• *Companhia:* {voo.companhia} (Voo Direto)
• *Preço Atual:* *R$ {voo.preco_brl:.2f}* ida e volta por pessoa
• *Média Histórica:* R$ {voo.preco_historico_brl:.2f}
• *Economia Real:* *{voo.desconto_percentual}% OFF* (Você poupa *R$ {voo.economia_liquida_brl:.2f}* por passageiro!)
• *Bagagem:* Mala de mão de 10kg inclusa

🔗 *Link Direto no Google Flights:*
{voo.url_reserva}

---
_AeroFolga — Vespasiano Labs | Inteligência Passiva de Viagens_"""
