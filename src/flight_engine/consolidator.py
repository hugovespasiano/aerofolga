"""
consolidator.py — AeroFolga / Vespasiano Labs
Motor de Consolidação Multi-Buscador e Arbitragem Inteligente:
Conecta Google Flights + Kiwi.com + Skiplagged + Amadeus GDS
e utiliza o Agente Árbitro para deduplicar e eleger a menor tarifa absoluta.
"""

from typing import List, Optional
from flight_engine.arbitro import AgenteArbitroVoos, OfertaNormalizada
from flight_engine.radar_voos import consultar_voo_com_blindagem
from flight_engine.providers.skiplagged import buscar_skiplagged
from flight_engine.providers.kiwi_provider import buscar_kiwi
from flight_engine.providers.amadeus_provider import AmadeusClient


def consolidar_todos_os_motores(
    origem: str,
    destino: str,
    data_ida: str,
    data_volta: str
) -> Optional[OfertaNormalizada]:
    """
    Dispara a busca simultânea em todos os motores conectados,
    deduplica os resultados e arbitra o melhor preço.
    """
    todas_ofertas: List[OfertaNormalizada] = []

    # 1. MOTOR 1: Google Flights (Pure Airline Inventory com blindagem profunda)
    try:
        gf = consultar_voo_com_blindagem(origem, destino, data_ida, data_volta)
        if gf and gf.get("preco"):
            todas_ofertas.append(OfertaNormalizada(
                motor="Google Flights",
                origem=origem,
                destino=destino,
                data_ida=data_ida,
                data_volta=data_volta,
                preco_brl=float(gf["preco"]),
                cia_aerea=gf.get("companhia", "Cia Aérea"),
                horario_ida=gf.get("horario_ida", ""),
                horario_volta=gf.get("horario_volta", ""),
                num_escalas=0,
                duracao_conexao_horas=0.0,
                duracao_total_horas=2.0,
                url_reserva=gf["url"],
                tipo_tarifa="REGULAR"
            ))
    except Exception:
        pass

    # 2. MOTOR 2: Kiwi.com (Virtual Interlining - Combos Multicompanhia)
    try:
        kw_list = buscar_kiwi(origem, destino, data_ida, data_volta)
        for kw in kw_list:
            todas_ofertas.append(OfertaNormalizada(
                motor="Kiwi (Virtual Interlining)",
                origem=origem,
                destino=destino,
                data_ida=data_ida,
                data_volta=data_volta,
                preco_brl=kw["preco_brl"],
                cia_aerea=kw["cia_aerea"],
                horario_ida="",
                horario_volta="",
                num_escalas=kw.get("num_escalas", 0),
                duracao_conexao_horas=0.0,
                duracao_total_horas=3.0,
                url_reserva=kw["url_reserva"],
                tipo_tarifa="COMBO_MULTICIA" if kw.get("is_combo") else "REGULAR"
            ))
    except Exception:
        pass

    # 3. MOTOR 3: Skiplagged (Tarifas de Cidade Oculta)
    try:
        skip_list = buscar_skiplagged(origem, destino, data_ida, data_volta)
        for sk in skip_list:
            todas_ofertas.append(OfertaNormalizada(
                motor="Skiplagged",
                origem=origem,
                destino=destino,
                data_ida=data_ida,
                data_volta=data_volta,
                preco_brl=float(sk["preco_pessoa"]),
                cia_aerea=f"{sk.get('companhia', 'Cia')} (🎒 Cidade Oculta - Apenas Mala de Mão)",
                horario_ida=sk.get("horario_ida", ""),
                horario_volta=sk.get("horario_volta", ""),
                num_escalas=sk.get("num_escalas", 0),
                duracao_conexao_horas=sk.get("duracao_conexao_horas", 0.0),
                duracao_total_horas=sk.get("duracao_total_horas", 3.0),
                url_reserva=sk["url"],
                tipo_tarifa="SKIPLAGGED",
                bagagem_mao_inclusa=True
            ))
    except Exception:
        pass

    # 4. MOTOR 4: Amadeus GDS
    try:
        amadeus = AmadeusClient()
        amd_list = amadeus.buscar_voos(origem, destino, data_ida, data_volta)
        for am in amd_list:
            todas_ofertas.append(OfertaNormalizada(
                motor="Amadeus GDS",
                origem=origem,
                destino=destino,
                data_ida=data_ida,
                data_volta=data_volta,
                preco_brl=am["preco_brl"],
                cia_aerea=am["cia_aerea"],
                horario_ida="",
                horario_volta="",
                num_escalas=0,
                duracao_conexao_horas=0.0,
                duracao_total_horas=2.0,
                url_reserva=am["url_reserva"],
                tipo_tarifa="REGULAR"
            ))
    except Exception:
        pass

    # Arbitragem e Deduplicação Inteligente
    arbitro = AgenteArbitroVoos()
    campeao = arbitro.arbitrar_e_desduplicar(todas_ofertas)
    return campeao
