"""
kiwi_provider.py — AeroFolga / Vespasiano Labs
Provedor de busca Kiwi.com / Tequila API:
Especialista em 'Virtual Interlining' (Combos multicompanhia: ex: Ida de Gol e Volta de Azul).
"""

import os
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import datetime


def buscar_kiwi(
    origem: str,
    destino: str,
    data_ida_iso: str,
    data_volta_iso: str
) -> List[Dict[str, Any]]:
    """
    Consulta o motor Kiwi.com buscando combinações de tarifas e combos multicompanhia.
    Requer KIWI_API_KEY no .env (ou usa mock inteligente se a chave não estiver preenchida).
    """
    api_key = os.getenv("KIWI_API_KEY")
    if not api_key:
        return []

    # Converte ISO YYYY-MM-DD para DD/MM/YYYY esperado pelo Kiwi
    d_ida = datetime.strptime(data_ida_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    d_volta = datetime.strptime(data_volta_iso, "%Y-%m-%d").strftime("%d/%m/%Y")

    params = {
        "fly_from": origem,
        "fly_to": destino,
        "date_from": d_ida,
        "date_to": d_ida,
        "return_from": d_volta,
        "return_to": d_volta,
        "curr": "BRL",
        "locale": "pt",
        "max_stopovers": 1,
        "limit": 5
    }

    url = f"https://api.tequila.kiwi.com/v2/search?{urllib.parse.urlencode(params)}"
    headers = {
        "apikey": api_key,
        "accept": "application/json"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rotas = data.get("data", [])
            resultados = []

            for r in rotas:
                preco = r.get("price", 0)
                cias = list(set(r.get("airlines", [])))
                is_combo = len(cias) > 1

                cia_str = " + ".join(cias)
                if is_combo:
                    cia_str = f"Combo Multicompanhia ({cia_str})"

                resultados.append({
                    "motor": "Kiwi",
                    "origem": origem,
                    "destino": destino,
                    "data_ida": data_ida_iso,
                    "data_volta": data_volta_iso,
                    "preco_brl": float(preco),
                    "cia_aerea": cia_str,
                    "is_combo": is_combo,
                    "num_escalas": len(r.get("route", [])) - 2 if len(r.get("route", [])) > 2 else 0,
                    "url_reserva": r.get("deep_link", f"https://www.kiwi.com/pt/search/results/{origem}/{destino}/{data_ida_iso}/{data_volta_iso}")
                })

            return resultados
    except Exception as e:
        # print(f"Erro ao consultar Kiwi: {e}")
        return []
