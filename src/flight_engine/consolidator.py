"""
consolidator.py — AeroFolga / Vespasiano Labs
Consolidador Multi-Provedores: Google Flights + Skiplagged (Hidden-City).
Compara múltiplos motores em tempo real e escolhe a menor tarifa absoluta real em BRL.
"""

from typing import Dict, Any, Optional
from flight_engine.radar_voos import consultar_voo_com_blindagem
from flight_engine.providers.skiplagged import buscar_skiplagged
from flight_engine.filtros_tilli import PropostaVoo


def buscar_menor_tarifa_multiprovedor(
    origem: str,
    destino: str,
    data_ida: str,
    data_volta: str,
    preco_historico: float = 1200.0
) -> Optional[PropostaVoo]:
    """
    Consulta o Google Flights e o Skiplagged simultaneamente, selecionando a menor tarifa real em BRL.
    """
    candidatos = []

    # 1. Provedor Google Flights (com blindagem profunda de payload)
    gf_res = consultar_voo_com_blindagem(origem, destino, data_ida, data_volta)
    if gf_res and gf_res.get("preco"):
        candidatos.append({
            "provedor": "Google Flights",
            "preco": float(gf_res["preco"]),
            "cia": gf_res.get("companhia", "Cia Aérea"),
            "url": gf_res["url"],
            "hidden_city": False,
            "horario_ida": gf_res.get("horario_ida", ""),
            "horario_volta": gf_res.get("horario_volta", ""),
            "num_escalas": 0,
            "duracao_conexao_horas": 0.0,
            "duracao_total_viagem_horas": 2.0
        })

    # 2. Provedor Skiplagged (Tarifas Ocultas / Carry-on Friendly - Auditado com cotação ao vivo)
    try:
        skip_res = buscar_skiplagged(origem, destino, data_ida, data_volta)
        if skip_res:
            melhor_skip = skip_res[0]
            preco_skip_brl = float(melhor_skip["preco_pessoa"])

            candidatos.append({
                "provedor": "Skiplagged",
                "preco": preco_skip_brl,
                "cia": melhor_skip.get("companhia", "Skiplagged Deal"),
                "url": melhor_skip["url"],
                "hidden_city": melhor_skip.get("hidden_city", False),
                "horario_ida": melhor_skip.get("horario_ida", ""),
                "horario_volta": melhor_skip.get("horario_volta", ""),
                "num_escalas": melhor_skip.get("num_escalas", 0),
                "duracao_conexao_horas": melhor_skip.get("duracao_conexao_horas", 0.0),
                "duracao_total_viagem_horas": melhor_skip.get("duracao_total_horas", 2.5)
            })
    except Exception as e:
        print(f"Erro ao consultar Skiplagged: {e}")

    if not candidatos:
        return None

    # Vence a menor tarifa real absoluta em BRL
    campeao = min(candidatos, key=lambda x: x["preco"])

    cia_rotulo = campeao["cia"]
    if campeao["hidden_city"]:
        cia_rotulo += " (🎒 Tarifa Oculta Skiplagged - Apenas Mochila/Mala de Mão)"

    return PropostaVoo(
        origem=origem,
        destino=destino,
        data_ida=data_ida,
        data_volta=data_volta,
        companhia=f"{cia_rotulo} via {campeao['provedor']}",
        preco_brl=campeao["preco"],
        preco_historico_brl=preco_historico,
        num_escalas=campeao["num_escalas"],
        duracao_conexao_horas=campeao["duracao_conexao_horas"],
        duracao_total_viagem_horas=campeao["duracao_total_viagem_horas"],
        troca_aeroporto=False,
        mala_de_mao_inclusa=True,
        chega_no_dia_seguinte=False,
        url_reserva=campeao["url"],
        horario_ida=campeao.get("horario_ida", ""),
        horario_volta=campeao.get("horario_volta", "")
    )


if __name__ == "__main__":
    p = buscar_menor_tarifa_multiprovedor("GIG", "CWB", "2026-12-30", "2027-01-03", 1200.0)
    if p:
        print(f"Campeão CWB: {p.preco_brl} via {p.companhia}")
