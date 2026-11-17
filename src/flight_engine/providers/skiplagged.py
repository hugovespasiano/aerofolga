"""
skiplagged.py — AeroFolga / Vespasiano Labs
Integração com Skiplagged API para busca de passagens com tarifas ocultas (Hidden-City)
e voos convencionais para passageiros com bagagem de mão/mochila.

Garante:
1. Captura de preços reais em USD e conversão para BRL com cotação ao vivo.
2. Combinação correta de Ida + Volta para viagens de ida e volta (round trip).
3. Aplicação rigorosa dos Filtros Tilli em cada trecho (máx 1 escala, espera 1h-4h, duração máx 8h).
"""

import urllib.request
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


def obter_taxa_dolar() -> float:
    """Obtém a taxa comercial USD-BRL em tempo real com fallback seguro."""
    try:
        req = urllib.request.Request(
            "https://economia.awesomeapi.com.br/json/last/USD-BRL",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return float(data["USDBRL"]["bid"])
    except Exception:
        return 5.80


def _parse_trecho(
    it_item: list,
    aeroporto_origem: str,
    aeroporto_destino: str,
    flights_dict: dict,
    max_escalas: int = 1,
    min_escala_horas: float = 1.0,
    max_escala_horas: float = 4.0,
    max_duracao_total_horas: float = 8.0
) -> Optional[Dict[str, Any]]:
    """
    Decodifica um trecho (ida ou volta) do Skiplagged e audita contra as travas de conforto.
    """
    if not it_item or len(it_item) < 4:
        return None

    price_cents = it_item[0][0] if isinstance(it_item[0], list) and len(it_item[0]) > 0 else None
    if price_cents is None or price_cents <= 0:
        return None

    eh_hidden_city = len(it_item[1]) > 0 if len(it_item) > 1 else False
    flight_key = it_item[3] if len(it_item) > 3 else None

    if not flight_key or flight_key not in flights_dict:
        return None

    raw_segments = flights_dict[flight_key][0]
    
    # Se for hidden city, o passageiro só viaja até o aeroporto_destino
    segments = []
    for s in raw_segments:
        segments.append(s)
        if s[3] == aeroporto_destino:
            break

    if not segments:
        return None

    # Cálculo dos tempos de conexão
    layovers = []
    for i in range(len(segments) - 1):
        try:
            arr = datetime.fromisoformat(segments[i][4])
            dep_next = datetime.fromisoformat(segments[i + 1][2])
            layover_h = (dep_next - arr).total_seconds() / 3600.0
            layovers.append(layover_h)
        except Exception:
            return None

    try:
        t_inicio = datetime.fromisoformat(segments[0][2])
        t_fim = datetime.fromisoformat(segments[-1][4])
        duracao_total_h = (t_fim - t_inicio).total_seconds() / 3600.0
    except Exception:
        return None

    stops = len(segments) - 1
    max_escala = max(layovers) if layovers else 0.0
    min_escala = min(layovers) if layovers else 0.0

    # Aplicação rígida dos Filtros Tilli
    if stops > max_escalas:
        return None
    if stops == 1:
        if max_escala > max_escala_horas or min_escala < min_escala_horas:
            return None
    if duracao_total_h > max_duracao_total_horas:
        return None

    cia_codigo = segments[0][0][:2] if segments[0][0] else "XX"
    cia_map = {"G3": "GOL", "LA": "LATAM", "AD": "Azul", "AR": "Aerolíneas Argentinas"}
    cia_nome = cia_map.get(cia_codigo, cia_codigo)

    dep_time_str = segments[0][2][11:16] if len(segments[0][2]) >= 16 else ""
    arr_time_str = segments[-1][4][11:16] if len(segments[-1][4]) >= 16 else ""

    return {
        "price_cents": price_cents,
        "stops": stops,
        "layover_hours": max_escala,
        "total_duration_hours": duracao_total_h,
        "dep_time": dep_time_str,
        "arr_time": arr_time_str,
        "cia": cia_nome,
        "hidden_city": eh_hidden_city,
        "origem": segments[0][1],
        "destino": segments[-1][3]
    }


def buscar_skiplagged(
    origem: str,
    destino: str,
    data_ida: str,
    data_volta: str
) -> List[Dict[str, Any]]:
    """
    Consulta o Skiplagged, combina Ida + Volta, valida travas de conforto e converte USD -> BRL real.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }
    url = f"https://skiplagged.com/api/search.php?from={origem}&to={destino}&depart={data_ida}&return={data_volta}&poll=true"
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        flights_dict = data.get("flights", {})
        departs = data.get("depart", [])
        returns = data.get("return", [])

        if not departs:
            return []

        # Audita trechos de ida
        idas_validas = []
        for it in departs:
            parsed = _parse_trecho(it, origem, destino, flights_dict)
            if parsed:
                idas_validas.append(parsed)

        # Se for busca de ida e volta e tiver retornos
        voltas_validas = []
        if returns:
            for it in returns:
                parsed = _parse_trecho(it, destino, origem, flights_dict)
                if parsed:
                    voltas_validas.append(parsed)

        if not idas_validas or (returns and not voltas_validas):
            return []

        # Seleciona o melhor trecho de ida e melhor de volta
        melhor_ida = min(idas_validas, key=lambda x: x["price_cents"])
        melhor_volta = min(voltas_validas, key=lambda x: x["price_cents"]) if voltas_validas else None

        total_cents = melhor_ida["price_cents"]
        if melhor_volta:
            total_cents += melhor_volta["price_cents"]

        taxa_dolar = obter_taxa_dolar()
        preco_usd = total_cents / 100.0
        preco_brl = round(preco_usd * taxa_dolar, 2)

        cia_final = melhor_ida["cia"]
        if melhor_volta and melhor_volta["cia"] != melhor_ida["cia"]:
            cia_final = f"{melhor_ida['cia']} / {melhor_volta['cia']}"

        tem_hidden_city = melhor_ida["hidden_city"] or (melhor_volta["hidden_city"] if melhor_volta else False)

        max_escalas = melhor_ida["stops"]
        if melhor_volta:
            max_escalas = max(max_escalas, melhor_volta["stops"])

        max_conexao = melhor_ida["layover_hours"]
        if melhor_volta:
            max_conexao = max(max_conexao, melhor_volta["layover_hours"])

        duracao_total = melhor_ida["total_duration_hours"]
        if melhor_volta:
            duracao_total += melhor_volta["total_duration_hours"]

        url_skiplagged = f"https://skiplagged.com/flights/{origem}/{destino}/{data_ida}/{data_volta}"

        resultado = {
            "provedor": "Skiplagged",
            "origem": origem,
            "destino": destino,
            "data_ida": data_ida,
            "data_volta": data_volta,
            "preco_pessoa": preco_brl,
            "preco_usd": preco_usd,
            "taxa_dolar": taxa_dolar,
            "hidden_city": tem_hidden_city,
            "companhia": cia_final,
            "num_escalas": max_escalas,
            "duracao_conexao_horas": round(max_conexao, 1),
            "duracao_total_horas": round(duracao_total, 1),
            "horario_ida": f"{melhor_ida['dep_time']} ➔ {melhor_ida['arr_time']}",
            "horario_volta": f"{melhor_volta['dep_time']} ➔ {melhor_volta['arr_time']}" if melhor_volta else "",
            "url": url_skiplagged
        }

        return [resultado]

    except Exception as e:
        print(f"Erro Skiplagged: {e}")
        return []


if __name__ == "__main__":
    res = buscar_skiplagged("GIG", "CWB", "2026-12-30", "2027-01-03")
    print("Resultado Skiplagged CWB:", res)
