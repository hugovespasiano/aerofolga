"""
amadeus_provider.py — AeroFolga / Vespasiano Labs
Provedor de busca Amadeus for Developers (GDS Oficial):
Acesso direto ao inventário oficial das companhias aéreas sem intermediários.
"""

import os
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional


class AmadeusClient:
    def __init__(self):
        self.client_id = os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
        self.token = None

    def _obter_token(self) -> Optional[str]:
        if not self.client_id or not self.client_secret:
            return None

        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        data = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                self.token = res.get("access_token")
                return self.token
        except Exception:
            return None

    def buscar_voos(self, origem: str, destino: str, data_ida: str, data_volta: str) -> List[Dict[str, Any]]:
        token = self._obter_token()
        if not token:
            return []

        params = {
            "originLocationCode": origem,
            "destinationLocationCode": destino,
            "departureDate": data_ida,
            "returnDate": data_volta,
            "adults": 1,
            "currencyCode": "BRL",
            "max": 5
        }

        url = f"https://test.api.amadeus.com/v2/shopping/flight-offers?{urllib.parse.urlencode(params)}"
        headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                ofertas = []
                for item in data.get("data", []):
                    preco = float(item.get("price", {}).get("total", 0))
                    ofertas.append({
                        "motor": "Amadeus GDS",
                        "origem": origem,
                        "destino": destino,
                        "data_ida": data_ida,
                        "data_volta": data_volta,
                        "preco_brl": preco,
                        "cia_aerea": "Tarifa GDS Corporativa",
                        "url_reserva": f"https://www.google.com/travel/flights?q=Flights%20to%20{destino}%20from%20{origem}%20on%20{data_ida}%20through%20{data_volta}"
                    })
                return ofertas
        except Exception:
            return []
