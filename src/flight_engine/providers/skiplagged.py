import urllib.request
import json
from typing import Dict, Any, List, Optional

def buscar_skiplagged(origem: str, destino: str, data_ida: str, data_volta: str) -> List[Dict[str, Any]]:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01'
    }
    url = f"https://skiplagged.com/api/search.php?from={origem}&to={destino}&depart={data_ida}&return={data_volta}&poll=true"
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            
            flights_dict = data.get('flights', {})
            itineraries = data.get('depart', [])
            
            resultados = []
            for it in itineraries:
                # it: [ [price_cents, ...], [hidden_city_info], flight_key_out, flight_key_in ]
                if not it or len(it) < 4:
                    continue
                preco_cents = it[0][0] if isinstance(it[0], list) and len(it[0]) > 0 else 0
                preco_brl = preco_cents / 100.0  # Em BRL na consulta BR ou USD aproximado
                
                eh_hidden_city = len(it[1]) > 0 if len(it) > 1 else False
                
                key_out = it[2] if len(it) > 2 else ""
                key_in = it[3] if len(it) > 3 else ""
                
                voo_out = flights_dict.get(key_out, [])
                cia = "Cia"
                if voo_out and len(voo_out) > 0 and len(voo_out[0]) > 0:
                    cia = voo_out[0][0][0][:2]  # código da cia
                
                url_skiplagged = f"https://skiplagged.com/flights/{origem}/{destino}/{data_ida}/{data_volta}"
                
                resultados.append({
                    "provedor": "Skiplagged",
                    "origem": origem,
                    "destino": destino,
                    "preco_pessoa": preco_brl,
                    "hidden_city": eh_hidden_city,
                    "companhia": cia,
                    "url": url_skiplagged
                })
            
            return resultados
    except Exception as e:
        print(f"Erro Skiplagged: {e}")
        return []

if __name__ == "__main__":
    res = buscar_skiplagged("GIG", "CWB", "2026-12-30", "2027-01-03")
    print(f"Skiplagged encontrou {len(res)} opções.")
    if res:
        print("Menor opção Skiplagged:", min(res, key=lambda x: x["preco_pessoa"]))
