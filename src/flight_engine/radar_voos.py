"""
radar_voos.py — AeroFolga / Vespasiano Labs
Motor de busca e montagem de URLs do Google Flights para as janelas do casal.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from flight_engine.filtros_tilli import PropostaVoo, auditar_voo_pelos_4_pilares


def gerar_link_google_flights(origem: str, destino: str, data_ida: str, data_volta: str) -> str:
    """
    Gera uma URL direta e funcional para o Google Flights com a rota e as datas exatas.
    """
    return f"https://www.google.com/travel/flights?q=Flights%20to%20{destino}%20from%20{origem}%20on%20{data_ida}%20through%20{data_volta}"


def carregar_destinos_homologados(caminho_destinos: str = "data/destinos.json") -> List[Dict[str, Any]]:
    """Carrega as rotas cadastradas em destinos.json."""
    path = Path(caminho_destinos)
    if not path.exists():
        # Fallback se executado de src/
        path = Path(__file__).parent.parent.parent / "data" / "destinos.json"

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def simular_radar_na_janela(
    inicio_iso: str,
    fim_iso: str,
    destinos: Optional[List[Dict[str, Any]]] = None
) -> List[PropostaVoo]:
    """
    Gera oportunidades de voo para a janela especificada, aplicando os 4 Pilares.
    """
    if destinos is None:
        destinos = carregar_destinos_homologados()

    oportunidades_aprovadas: List[PropostaVoo] = []

    for d in destinos:
        origens = d.get("origens_aceitas", ["GIG", "GRU"])
        destino_codigo = d["destino_codigo"]
        preco_historico = d["preco_medio_historico_brl"]
        gatilho_maximo = d["gatilho_alerta_maximo_brl"]

        for origem in origens[:2]:  # Simula principais origens (GIG / GRU)
            # Simula um preço promocional atípico abaixo do gatilho
            preco_simulado = gatilho_maximo - 35.0  # Exemplo de tarifa desovada

            link = gerar_link_google_flights(origem, destino_codigo, inicio_iso, fim_iso)
            proposta = PropostaVoo(
                origem=origem,
                destino=destino_codigo,
                data_ida=inicio_iso,
                data_volta=fim_iso,
                companhia="LATAM" if origem == "GIG" else "Gol / Flybondi",
                preco_brl=preco_simulado,
                preco_historico_brl=preco_historico,
                tem_conexao=False,
                duracao_conexao_horas=0.0,
                troca_aeroporto=False,
                mala_de_mao_inclusa=True,
                url_reserva=link
            )

            aprovado, motivo = auditar_voo_pelos_4_pilares(proposta)
            if aprovado:
                oportunidades_aprovadas.append(proposta)

    return oportunidades_aprovadas
