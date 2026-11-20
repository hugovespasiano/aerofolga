"""
formatador_alerta.py — AeroFolga / Vespasiano Labs
Diagramação orientada à tomada de decisão rápida e economia transparente:
1. VALOR TOTAL CASAL E TARIFA (Topo Absoluto)
2. BÚSSOLA DE PREÇO: % DE ECONOMIA + FAIXA HISTÓRICA (Médio, Mínimo e Máximo)
3. ORIGEM ➔ DESTINO
4. DATAS E HORÁRIOS DOS VOOS
5. ÔNIBUS VOLTA REDONDA (Cidade do Aço com 3h a 3h30 de folga líquida no saguão)
6. LINK DIRETO GOOGLE VOOS
"""

import json
from pathlib import Path
from typing import Optional
from calendar_engine.calculadora_janelas import JanelaViagem
from flight_engine.filtros_tilli import PropostaVoo
from decision_engine.custo_porta_a_porta import calcular_logistica


def carregar_referencia_historica() -> dict:
    caminho = Path(__file__).parent.parent.parent / "data" / "tabela_referencia.json"
    if caminho.exists():
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def sugerir_horario_onibus(horario_ida: str, aeroporto: str) -> str:
    """
    Calcula o horário recomendado de embarque na Rodoviária de Volta Redonda
    garantindo entre 3h00 e 3h30 de antecedência LÍQUIDA no aeroporto.
    """
    if aeroporto in ("GIG", "SDU"):
        if horario_ida and "➔" in horario_ida:
            try:
                hora_partida_str = horario_ida.split("➔")[0].strip()
                h, m = map(int, hora_partida_str.split(":"))
                # Subtrai 5h45min (345 min) para garantir 3h15 de folga líquida no aeroporto
                total_min = h * 60 + m - 345
                if total_min < 0:
                    total_min += 24 * 60
                h_bus = total_min // 60
                m_bus = (total_min % 60 // 30) * 30  # Blocos de 30 min
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
    modo: str = "html",
    alavancagem_tre: Optional[str] = None
) -> str:
    """
    Gera a mensagem com a nova diagramação solicitada pelo Hugo:
    Valores, % de Economia e Faixa Histórica nas PRIMEIRAS linhas.
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

    # Análise de Ancoragem Histórica e Economia
    ref_map = carregar_referencia_historica()
    ref = ref_map.get(destino, {})

    preco_medio = float(ref.get("preco_medio_tipico", 1000.0))
    piso_alta = float(ref.get("piso_alta_temporada", 700.0))
    piso_baixa = float(ref.get("piso_baixa_temporada", 300.0))
    teto_alta = float(ref.get("teto_maximo_alta", 1800.0))
    meses_baratos = ref.get("meses_mais_baratos", "Maio e Agosto")

    if preco_medio > tarifa_pessoa:
        economia_pct = int(round(((preco_medio - tarifa_pessoa) / preco_medio) * 100))
        economia_casal = (preco_medio - tarifa_pessoa) * 2
        bloco_economia_html = f"""🏷️ <b>ECONOMIA: {economia_pct}% DE DESCONTO</b> (Você poupa <b>R$ {economia_casal:,.2f}</b> no casal!)
   • <b>Preço Médio Típico desta época:</b> R$ {preco_medio:,.2f}/pessoa (R$ {preco_medio*2:,.2f} casal)
   • <b>Faixa Histórica:</b> Piso Feriadão: R$ {piso_alta:,.2f} | Teto em alta: R$ {teto_alta:,.2f}
   • <i>Menor do ano (baixa estação morta): R$ {piso_baixa:,.2f} ({meses_baratos})</i>"""

        bloco_economia_txt = f"""🏷️ *ECONOMIA: {economia_pct}% DE DESCONTO* (Você poupa *R$ {economia_casal:,.2f}* no casal!)
   • *Preço Médio Típico desta época:* R$ {preco_medio:,.2f}/pessoa (R$ {preco_medio*2:,.2f} casal)
   • *Faixa Histórica:* Piso Feriadão: R$ {piso_alta:,.2f} | Teto em alta: R$ {teto_alta:,.2f}
   • _Menor do ano (baixa estação morta): R$ {piso_baixa:,.2f} ({meses_baratos})_"""
    else:
        bloco_economia_html = f"""🏷️ <b>MERCADO EM ALTA:</b> R$ {tarifa_pessoa:,.2f} vs Médio de R$ {preco_medio:,.2f}"""
        bloco_economia_txt = f"""🏷️ *MERCADO EM ALTA:* R$ {tarifa_pessoa:,.2f} vs Médio de R$ {preco_medio:,.2f}"""

    if alavancagem_tre:
        bloco_tipo_html = f"🟡 <b>TIPO DE FOLGA:</b> Alavancado TRE ({alavancagem_tre})"
        bloco_tipo_txt = f"🟡 *TIPO DE FOLGA:* Alavancado TRE ({alavancagem_tre})"
    else:
        bloco_tipo_html = "🟢 <b>TIPO DE FOLGA:</b> Feriado / Ponto Facultativo (100% Puro — 0 folgas TRE)"
        bloco_tipo_txt = "🟢 *TIPO DE FOLGA:* Feriado / Ponto Facultativo (100% Puro — 0 folgas TRE)"

    if modo == "html":
        return f"""💰 <b>R$ {custo_final_casal:,.2f} TOTAL CASAL</b> (Porta a Porta)
   ↳ Passagens Casal: R$ {passagens_casal:,.2f} (R$ {tarifa_pessoa:,.2f}/pessoa ida e volta)
   ↳ Logística VR: R$ {custo_logistica:,.2f} (Cidade do Aço/Cometa + Transfer {origem})

{bloco_economia_html}

📍 <b>ROTA:</b> {origem_nome} ({origem}) ➔ {destino_nome} ({destino})
📅 <b>DATAS:</b> {datas_label}
{bloco_tipo_html}
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
   ↳ Logística VR: R$ {custo_logistica:,.2f} (Cidade do Aço/Cometa + Transfer {origem})

{bloco_economia_txt}

📍 *ROTA:* {origem_nome} ({origem}) ➔ {destino_nome} ({destino})
📅 *DATAS:* {datas_label}
{bloco_tipo_txt}
⏰ *HORÁRIOS DOS VOOS ({cia_aerea}):*
   • *Ida:* {horario_ida}
   • *Volta:* {horario_volta}
   • Bagagem de mão 10kg + mochila inclusas

🚌 *ÔNIBUS VOLTA REDONDA:*
   • {onibus_detalhe}

🔗 *RESERVA GOOGLE VOOS:*
{url_reserva}"""
