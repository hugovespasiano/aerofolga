"""
formatador_alerta.py — AeroFolga / Vespasiano Labs
Formatação persuasiva, objetiva e sem prolixidade das notificações para o casal,
seguindo rigorosamente os padrões de transparência:
- Saída ➔ Destino
- Datas e Horários
- Ônibus Cidade do Aço (margem Dutra / Serra das Araras)
- Separação transparente: Por Pessoa | Total Casal | Logística VR | Custo Final Real
"""

from calendar_engine.calculadora_janelas import JanelaViagem
from flight_engine.filtros_tilli import PropostaVoo
from decision_engine.custo_porta_a_porta import calcular_logistica


def sugerir_horario_onibus(horario_ida: str, aeroporto: str) -> str:
    """
    Calcula o horário recomendado de embarque na Rodoviária de Volta Redonda
    com margem de 4h a 5h de segurança para a Dutra e Serra das Araras.
    """
    if aeroporto in ("GIG", "SDU"):
        if horario_ida and "➔" in horario_ida:
            try:
                hora_partida_str = horario_ida.split("➔")[0].strip()
                h, m = map(int, hora_partida_str.split(":"))
                # Subtrai 4h30min de antecedência
                total_min = h * 60 + m - 270
                if total_min < 0:
                    total_min += 24 * 60
                h_bus = total_min // 60
                m_bus = (total_min % 60 // 30) * 30  # Arredonda para blocos de 30 min
                return f"Cidade do Aço às {h_bus:02d}:{m_bus:02d} (chegada com folga para raio-X e Serra das Araras)"
            except Exception:
                pass
        return "Cidade do Aço com 4h a 5h de antecedência do voo (margem de segurança Serra das Araras)"
    else:
        return "Viação Cometa (VR ➔ Tietê) no dia anterior + Pernoite de segurança em SP"


def formatar_alerta_whatsapp(janela: JanelaViagem, voo: PropostaVoo) -> str:
    """
    Formatação oficial de alta clareza do AeroFolga.
    """
    log = calcular_logistica(voo.origem)
    passagens_casal = voo.preco_brl * 2
    custo_logistico_casal = log.custo_logistico_total
    custo_final_casal = passagens_casal + custo_logistico_casal

    horarios_bloco = ""
    if voo.horario_ida:
        horarios_bloco += f"• *Horário Ida:* {voo.horario_ida}\n"
    if voo.horario_volta:
        horarios_bloco += f"• *Horário Volta:* {voo.horario_volta}\n"

    onibus_recomendado = sugerir_horario_onibus(voo.horario_ida, voo.origem)

    alavancagem_tre = ""
    if janela.custo_tre > 0:
        alavancagem_tre = f"\n💡 *Estratégia:* Conectado com {janela.custo_tre} folga(s) do TRE do Hugo."

    return f"""✈️ *[AeroFolga] Alerta Real de Viagem do Casal*

📍 *Rota:* {voo.origem} ➔ {voo.destino}
📅 *Datas:* {janela.to_dict()['periodo']} ({janela.dias_totais} dias livres){alavancagem_tre}
🛫 *Companhia:* {voo.companhia}
{horarios_bloco}• *Conexões:* {"Voo Direto" if voo.num_escalas == 0 else f"{voo.num_escalas} escala (espera humana de {voo.duracao_conexao_horas}h)"}
• *Bagagem:* Mochila e mala de mão inclusas

💰 *Detalhamento Transparente de Custos:*
• *Tarifa Aérea por pessoa:* *R$ {voo.preco_brl:.2f}* (Ida e Volta)
• *Passagens do Casal (2 pessoas):* *R$ {passagens_casal:.2f}*
• *Deslocamento Volta Redonda (Cidade do Aço + Uber):* R$ {custo_logistico_casal:.2f}
━━━━━━━━━━━━━━━━━━━━
🎯 *CUSTO FINAL REAL DO CASAL:* *R$ {custo_final_casal:.2f}*

🚌 *Logística Saindo de Volta Redonda:*
• *Recomendação:* {onibus_recomendado}

🔗 *Link Direto para Reserva:*
{voo.url_reserva}

---
_AeroFolga | Inteligência de Viagem sem Ilusão de Preço_"""
