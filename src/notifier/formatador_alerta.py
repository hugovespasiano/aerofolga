"""
formatador_alerta.py — AeroFolga / Vespasiano Labs
Diagramação orientada à ação imediata:
1. VALOR TOTAL CASAL E TARIFA (Topo Absoluto)
2. ORIGEM ➔ DESTINO
3. DATAS E HORÁRIOS DOS VOOS
4. ÔNIBUS VOLTA REDONDA (Cidade do Aço com margem de segurança Dutra/Serra)
5. LINK DIRETO GOOGLE VOOS
"""

from typing import Optional
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
                m_bus = (total_min % 60 // 30) * 30  # Blocos de 30 minutos
                return f"Cidade do Aço às {h_bus:02d}:{m_bus:02d} (chegada ~2h antes do voo, com folga para a Serra das Araras)"
            except Exception:
                pass
        return "Cidade do Aço com 4h a 5h de antecedência do voo (margem Dutra / Serra das Araras)"
    else:
        return "Viação Cometa (VR ➔ Tietê) no dia anterior + Pernoite de segurança em SP"


def formatar_alerta_novo_padrao(
    origem: str,
    origem_nome: str,
    destino: str,
    destino_nome: str,
    datas_label: str,
    tarifa_pessoa: float,
    cia_aerea: str,
    horario_ida: str,
    horario_volta: str,
    onibus_detalhe: str,
    url_reserva: str,
    modo: str = "html"
) -> str:
    """
    Gera a mensagem com a nova diagramação solicitada pelo Hugo:
    Valores e Rota nas PRIMEIRAS linhas.
    """
    passagens_casal = tarifa_pessoa * 2
    custo_logistica = 350.0 if origem in ("GIG", "SDU") else 1110.0
    custo_final_casal = passagens_casal + custo_logistica

    if modo == "html":
        return f"""💰 <b>R$ {custo_final_casal:,.2f} TOTAL CASAL</b> (Porta a Porta)
   ↳ Passagens Casal: R$ {passagens_casal:,.2f} (R$ {tarifa_pessoa:,.2f}/pessoa ida e volta)
   ↳ Logística VR: R$ {custo_logistica:,.2f} (Cidade do Aço + Uber {origem})

📍 <b>ROTA:</b> {origem_nome} ({origem}) ➔ {destino_nome} ({destino})
📅 <b>DATAS:</b> {datas_label}
⏰ <b>HORÁRIOS DOS VOOS ({cia_aerea}):</b>
   • <b>Ida:</b> {horario_ida}
   • <b>Volta:</b> {horario_volta}
   • Bagagem de mão 10kg + mochila inclusas

🚌 <b>ÔNIBUS VOLTA REDONDA:</b>
   • {onibus_detalhe}

🔗 <b>RESERVA GOOGLE VOOS:</b>
<a href="{url_reserva}">Abrir Voo no Google Flights</a>"""
    else:
        return f"""💰 *R$ {custo_final_casal:,.2f} TOTAL CASAL* (Porta a Porta)
   ↳ Passagens Casal: R$ {passagens_casal:,.2f} (R$ {tarifa_pessoa:,.2f}/pessoa ida e volta)
   ↳ Logística VR: R$ {custo_logistica:,.2f} (Cidade do Aço + Uber {origem})

📍 *ROTA:* {origem_nome} ({origem}) ➔ {destino_nome} ({destino})
📅 *DATAS:* {datas_label}
⏰ *HORÁRIOS DOS VOOS ({cia_aerea}):*
   • *Ida:* {horario_ida}
   • *Volta:* {horario_volta}
   • Bagagem de mão 10kg + mochila inclusas

🚌 *ÔNIBUS VOLTA REDONDA:*
   • {onibus_detalhe}

🔗 *RESERVA GOOGLE VOOS:*
{url_reserva}"""
