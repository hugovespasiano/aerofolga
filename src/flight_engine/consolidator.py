"""
consolidator.py — AeroFolga / Vespasiano Labs
Consolidador Multi-Provedores: Google Flights + Skiplagged (Hidden-City).
Compara múltiplos motores em tempo real e escolhe a menor tarifa absoluta.
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
    Consulta o Google Flights e o Skiplagged simultaneamente, selecionando a opção mais barata.
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
            "hidden_city": False
        })

    # 2. Provedor Skiplagged (Tarifas Ocultas / Carry-on Friendly)
    try:
        skip_res = buscar_skiplagged(origem, destino, data_ida, data_volta)
        if skip_res:
            melhor_skip = min(skip_res, key=lambda x: x["preco_pessoa"])
            # Se vier em USD converte para BRL aproximado (~5.80)
            preco_skip_brl = melhor_skip["preco_pessoa"]
            if preco_skip_brl < 400:  # Indicativo de USD
                preco_skip_brl = round(preco_skip_brl * 5.80, 2)

            candidatos.append({
                "provedor": "Skiplagged",
                "preco": float(preco_skip_brl),
                "cia": melhor_skip.get("companhia", "Skiplagged Deal"),
                "url": melhor_skip["url"],
                "hidden_city": melhor_skip.get("hidden_city", False)
            })
    except Exception as e:
        print(f"Erro ao consultar Skiplagged: {e}")

    if not candidatos:
        return None

    # Vence o menor preço absoluto
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
        num_escalas=0,
        duracao_conexao_horas=0.0,
        duracao_total_viagem_horas=2.0,
        troca_aeroporto=False,
        mala_de_mao_inclusa=True,
        chega_no_dia_seguinte=False,
        url_reserva=campeao["url"]
    )
