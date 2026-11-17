"""
radar_voos.py — AeroFolga / Vespasiano Labs
Motor de busca, montagem de URLs e BLINDAGEM DE PREÇO MÍNIMO do Google Flights.
Garante que o menor preço absoluto da tela seja sempre capturado.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from fast_flights import FlightQuery, Passengers, create_query, get_flights
from fast_flights.fetcher import fetch_flights_html
from flight_engine.filtros_tilli import PropostaVoo, auditar_voo_pelos_4_pilares


def extrair_menor_preco_absoluto_html(html: str) -> Optional[int]:
    """
    TRAVA DE SEGURANÇA 1: Varredura profunda no payload do Google Flights.
    O Google Flights costuma esconder as menores tarifas em abas separadas ('Menores Preços').
    Esta função audita todos os tokens de preço do payload e extrai o menor valor absoluto real.
    """
    matches = re.findall(r'\[\[null,(\d{3,5})\],"(?:Cj|[A-Za-z0-9_-])', html)
    if not matches:
        return None
    precos = [int(p) for p in matches if int(p) > 50]
    return min(precos) if precos else None


def consultar_voo_com_blindagem(
    origem: str,
    destino: str,
    data_ida: str,
    data_volta: str
) -> Optional[Dict[str, Any]]:
    """
    Consulta o voo com a trava de segurança ativa:
    Compara a lista parseada com a varredura profunda de HTML para impedir divergências de preço.
    """
    query = create_query(
        flights=[
            FlightQuery(date=data_ida, from_airport=origem, to_airport=destino),
            FlightQuery(date=data_volta, from_airport=destino, to_airport=origem)
        ],
        seat="economy",
        trip="round-trip",
        passengers=Passengers(adults=1),
        currency="BRL",
        language="pt-BR"
    )

    try:
        # 1. Busca HTML bruto e executa a trava de segurança
        html = fetch_flights_html(query)
        preco_minimo_blindado = extrair_menor_preco_absoluto_html(html)

        # 2. Busca lista estruturada
        res = get_flights(query)
        voos_lista = [f for f in res if f.price and f.price > 0] if res else []

        if not voos_lista and not preco_minimo_blindado:
            return None

        menor_lista = min(voos_lista, key=lambda x: x.price) if voos_lista else None
        preco_lista = menor_lista.price if menor_lista else 999999

        # 3. Auditoria de Divergência:
        # Se a trava identificou um preço menor que a lista (ex: 754 vs 856), o preço blindado prevalece!
        preco_final = preco_lista
        if preco_minimo_blindado and preco_minimo_blindado < preco_lista:
            preco_final = preco_minimo_blindado

        cia = menor_lista.airlines[0] if menor_lista and menor_lista.airlines else "Cia Aérea (Melhor Tarifa)"
        
        url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destino}%20from%20{origem}%20on%20{data_ida}%20through%20{data_volta}"

        return {
            "origem": origem,
            "destino": destino,
            "data_ida": data_ida,
            "data_volta": data_volta,
            "preco": preco_final,
            "blindagem_aplicada": preco_final < preco_lista,
            "companhia": cia,
            "url": url
        }
    except Exception as e:
        print(f"Erro na consulta blindada: {e}")
        return None
