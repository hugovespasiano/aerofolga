"""
formatador_alerta.py — AeroFolga / Vespasiano Labs
Diagramação orientada à ação imediata:
1. VALOR TOTAL CASAL E TARIFA (Topo Absoluto)
2. ORIGEM ➔ DESTINO
3. DATAS E HORÁRIOS DOS VOOS
4. ÔNIBUS VOLTA REDONDA (Cidade do Aço com 3h a 3h30 de folga no aeroporto + margem Serra)
5. LINK DIRETO GOOGLE VOOS
"""

from typing import Optional
from calendar_engine.calculadora_janelas import JanelaViagem
from flight_engine.filtros_tilli import PropostaVoo
from decision_engine.custo_porta_a_porta import calcular_logistica


def sugerir_horario_onibus(horario_ida: str, aeroporto: str) -> str:
    """
    Calcula o horário recomendado de embarque na Rodoviária de Volta Redonda
    garantindo entre 3h00 e 3h30 de antecedência LÍQUIDA no aeroporto
    além do tempo de trajeto (Serra das Araras + Dutra + Uber).
    Total de folga recomendada antes da decolagem: ~5h30 a 6h00.
    """
    if aeroporto in ("GIG", "SDU"):
        if horario_ida and "➔" in horario_ida:
            try:
                hora_partida_str = horario_ida.split("➔")[0].strip()
                h, m = map(int, hora_partida_str.split(":"))
                # Subtrai 5h45min (345 min) para garantir 3h15 de folga no aeroporto
                total_min = h * 60 + m - 345
                if total_min < 0:
                    total_min += 24 * 60
                h_bus = total_min // 60
                m_bus = (total_min % 60 // 30) * 30  # Blocos de 30 min (ex: 12:30, 13:00)
                return f"Embarque às {h_bus:02d}:{m_bus:02d} (Cidade do Aço - Rodoviária Francisco Torres). Chegada prevista ao {aeroporto} ~3h a 3h30 antes do voo, garantindo total tranquilidade contra retenções na Serra das Araras e filas no aeroporto."
            except Exception:
                pass
        return "Cidade do Aço com 5h30 a 6h de antecedência do voo (garante 3h a 3h30 de folga líquida no aeroporto)"
    elif aeroporto == "CGH":
        return "Viação Cometa (VR ➔ Terminal Tietê) + Uber Tietê ➔ Congonhas (~35 min pelo Corredor Norte-Sul). Recomendado sair com 8h a 9h de antecedência do voo."
    elif aeroporto == "GRU":
        return "Viação Cometa (VR ➔ Terminal Tietê) + Uber Tietê ➔ Guarulhos (~35 min). Recomendado sair com 8h a 9h de antecedência do voo."
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
    if origem in ("GIG", "SDU"):
        custo_logistica = 350.0
    elif origem == "CGH":
        custo_logistica = 730.0
    elif origem == "GRU":
        custo_logistica = 760.0
    else:
        custo_logistica = 1110.0
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
