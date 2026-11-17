"""
radar_voos.py — AeroFolga / Vespasiano Labs
Motor de busca, montagem de URLs, TRAVA DE CONEXÃO HUMANA e BLINDAGEM DE PREÇO MÍNIMO.
Garante:
1. Máximo 1 escala (sem voos pinga-pinga)
2. Escala entre 1h e 4h (sem esperas de 6h ou pernoites de 24h no aeroporto)
3. Duração total máxima de 8h (sem odisseias de dia seguinte)
4. Menor preço absoluto capturado
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
    data_volta: str,
    max_escalas: int = 1,
    min_escala_minutos: int = 60,
    max_escala_minutos: int = 240,     # Máximo de 4 horas de espera!
    max_duracao_total_minutos: int = 480  # Máximo de 8 horas de viagem total!
) -> Optional[Dict[str, Any]]:
    """
    Consulta o voo aplicando a TRAVA RÍGIDA DE CONEXÃO HUMANA e a BLINDAGEM DE PREÇO.
    Elimina voos de 24 horas, pinga-pinga e escalas de 6+ horas.
    """
    query = create_query(
        flights=[
            FlightQuery(
                date=data_ida,
                from_airport=origem,
                to_airport=destino,
                max_stops=max_escalas,
                min_layover_minutes=min_escala_minutos,
                max_layover_minutes=max_escala_minutos,
                max_duration_minutes=max_duracao_total_minutos
            ),
            FlightQuery(
                date=data_volta,
                from_airport=destino,
                to_airport=origem,
                max_stops=max_escalas,
                min_layover_minutes=min_escala_minutos,
                max_layover_minutes=max_escala_minutos,
                max_duration_minutes=max_duracao_total_minutos
            )
        ],
        seat="economy",
        trip="round-trip",
        passengers=Passengers(adults=1),
        currency="BRL",
        language="pt-BR"
    )

    try:
        # 1. Busca HTML bruto e executa a trava de menor preço
        html = fetch_flights_html(query)
        preco_minimo_blindado = extrair_menor_preco_absoluto_html(html)

        # 2. Busca lista estruturada
        res = get_flights(query)
        voos_lista = [f for f in res if f.price and f.price > 0] if res else []

        if not voos_lista and not preco_minimo_blindado:
            return None

        menor_lista = min(voos_lista, key=lambda x: x.price) if voos_lista else None
        preco_lista = menor_lista.price if menor_lista else 999999

        # Preço final auditado
        preco_final = preco_lista
        if preco_minimo_blindado and preco_minimo_blindado < preco_lista:
            preco_final = preco_minimo_blindado

        cia = menor_lista.airlines[0] if menor_lista and menor_lista.airlines else "Cia Aérea"
        
        url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destino}%20from%20{origem}%20on%20{data_ida}%20through%20{data_volta}"

        return {
            "origem": origem,
            "destino": destino,
            "data_ida": data_ida,
            "data_volta": data_volta,
            "preco": preco_final,
            "blindagem_preco": preco_final < preco_lista,
            "trava_conexao_ativa": True,
            "max_espera_horas": max_escala_minutos / 60,
            "companhia": cia,
            "url": url
        }
    except Exception as e:
        print(f"Erro na consulta blindada: {e}")
        return None
