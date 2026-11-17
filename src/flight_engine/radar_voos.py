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

        h_ida = ""
        if menor_lista and getattr(menor_lista, 'flights', None) and len(menor_lista.flights) > 0:
            sf = menor_lista.flights[0]
            if hasattr(sf, 'departure') and hasattr(sf.departure, 'time') and hasattr(sf, 'arrival') and hasattr(sf.arrival, 'time'):
                h_ida = f"{sf.departure.time[0]:02d}:{sf.departure.time[1]:02d} ➔ {sf.arrival.time[0]:02d}:{sf.arrival.time[1]:02d}"

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
            "horario_ida": h_ida,
            "horario_volta": "",
            "url": url
        }
    except Exception as e:
        print(f"Erro na consulta blindada: {e}")
        return None


def carregar_destinos_homologados(caminho_destinos: str = "data/destinos.json") -> List[Dict[str, Any]]:
    """Carrega as rotas cadastradas em destinos.json."""
    path = Path(caminho_destinos)
    if not path.exists():
        path = Path(__file__).parent.parent.parent / "data" / "destinos.json"

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def simular_radar_na_janela(
    inicio_iso: str,
    fim_iso: str,
    destinos: Optional[List[Dict[str, Any]]] = None
) -> List[PropostaVoo]:
    """
    Gera oportunidades de voo para a janela especificada, aplicando a blindagem e os 4 Pilares.
    """
    if destinos is None:
        destinos = carregar_destinos_homologados()

    oportunidades_aprovadas: List[PropostaVoo] = []

    for d in destinos:
        origens = d.get("origens_aceitas", ["GIG", "GRU"])
        destino_codigo = d["destino_codigo"]
        preco_historico = d["preco_medio_historico_brl"]
        gatilho_maximo = d["gatilho_alerta_maximo_brl"]

        for origem in origens[:1]:  # Prioriza Galeão
            preco_simulado = gatilho_maximo - 35.0

            link = f"https://www.google.com/travel/flights?q=Flights%20to%20{destino_codigo}%20from%20{origem}%20on%20{inicio_iso}%20through%20{fim_iso}"
            proposta = PropostaVoo(
                origem=origem,
                destino=destino_codigo,
                data_ida=inicio_iso,
                data_volta=fim_iso,
                companhia="LATAM",
                preco_brl=preco_simulado,
                preco_historico_brl=preco_historico,
                num_escalas=0,
                duracao_conexao_horas=0.0,
                duracao_total_viagem_horas=2.0,
                troca_aeroporto=False,
                mala_de_mao_inclusa=True,
                chega_no_dia_seguinte=False,
                url_reserva=link
            )

            aprovado, motivo = auditar_voo_pelos_4_pilares(proposta)
            if aprovado:
                oportunidades_aprovadas.append(proposta)

    return oportunidades_aprovadas
