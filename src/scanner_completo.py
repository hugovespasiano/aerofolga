import sys
import time
import json
import concurrent.futures
from fast_flights import FlightQuery, Passengers, create_query, get_flights

DESTINOS = [
    {"cod": "CWB", "nome": "Curitiba"},
    {"cod": "VIX", "nome": "Vitória"},
    {"cod": "CNF", "nome": "Belo Horizonte"},
    {"cod": "FLN", "nome": "Florianópolis"},
    {"cod": "BSB", "nome": "Brasília"},
    {"cod": "SSA", "nome": "Salvador"},
    {"cod": "IGU", "nome": "Foz do Iguaçu"},
    {"cod": "NVT", "nome": "Navegantes"}
]

JANELAS = [
    # Natal
    ("2026-12-22", "2026-12-26", "Natal (22/12 a 26/12)"),
    ("2026-12-23", "2026-12-27", "Natal (23/12 a 27/12)"),
    ("2026-12-24", "2026-12-28", "Natal (24/12 a 28/12)"),
    # Entre Natal e Ano Novo
    ("2026-12-26", "2026-12-30", "Fim de Ano (26/12 a 30/12)"),
    # Réveillon
    ("2026-12-29", "2027-01-02", "Réveillon (29/12 a 02/01)"),
    ("2026-12-30", "2027-01-03", "Réveillon (30/12 a 03/01)"),
    ("2026-12-31", "2027-01-04", "Réveillon (31/12 a 04/01)"),
    # Janeiro
    ("2027-01-03", "2027-01-07", "Janeiro (03/01 a 07/01)"),
    ("2027-01-04", "2027-01-08", "Janeiro (04/01 a 08/01)"),
    ("2027-01-05", "2027-01-09", "Janeiro (05/01 a 09/01)"),
    ("2027-01-06", "2027-01-10", "Janeiro (06/01 a 10/01)")
]

def consultar_par(orig, dest, d_ida, d_volta, label):
    try:
        q = create_query(
            flights=[
                FlightQuery(date=d_ida, from_airport=orig, to_airport=dest),
                FlightQuery(date=d_volta, from_airport=dest, to_airport=orig)
            ],
            seat="economy",
            trip="round-trip",
            passengers=Passengers(adults=1),
            currency="BRL",
            language="pt-BR"
        )
        res = get_flights(q)
        if not res:
            return None
        valid = [f for f in res if f.price and f.price > 0]
        if not valid:
            return None
        
        # Filtra voos com max 1 conexão e menor preço
        melhor = min(valid, key=lambda x: x.price)
        
        # Horários de ida
        h_ida = ""
        if melhor.flights:
            f0 = melhor.flights[0]
            dep_t = f"{f0.departure.time[0]:02d}:{f0.departure.time[1]:02d}"
            arr_t = f"{f0.arrival.time[0]:02d}:{f0.arrival.time[1]:02d}"
            h_ida = f"{dep_t} ➔ {arr_t}"

        # Verifica escala
        num_escalas = len(melhor.flights) - 1

        url = f"https://www.google.com/travel/flights?q=Flights%20to%20{dest}%20from%20{orig}%20on%20{d_ida}%20through%20{d_volta}"

        return {
            "origem": orig,
            "destino": dest,
            "data_ida": d_ida,
            "data_volta": d_volta,
            "label": label,
            "preco": melhor.price,
            "cia": melhor.airlines[0] if melhor.airlines else "Cia Aérea",
            "horario_ida": h_ida,
            "escalas": num_escalas,
            "url": url
        }
    except Exception as e:
        return None

def main():
    tarefas = []
    # 1. Prioridade absoluta: Rio de Janeiro (GIG)
    for j in JANELAS:
        for d in DESTINOS:
            tarefas.append(("GIG", d["cod"], j[0], j[1], j[2]))
            
    # 2. Benchmark São Paulo (GRU) para comparar se compensa a barreira logística
    for j in [JANELAS[1], JANELAS[5], JANELAS[9]]: # amostra de Natal, Reveillon, Janeiro
        for d in ["CWB", "FLN", "SSA", "NVT"]:
            tarefas.append(("GRU", d, j[0], j[1], j[2]))

    print(f"Disparando {len(tarefas)} consultas reais ao Google Flights...")
    resultados = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futs = {executor.submit(consultar_par, *t): t for t in tarefas}
        for f in concurrent.futures.as_completed(futs):
            res = f.result()
            if res:
                resultados.append(res)
                print(f"✔ [{res['origem']} ➔ {res['destino']}] R$ {res['preco']} ({res['cia']}) - {res['label']}")

    # Ordena pelo menor preço
    resultados.sort(key=lambda x: x["preco"])

    with open("data/resultados_varredura_real.json", "w", encoding="utf-8") as out:
        json.dump(resultados, out, indent=2, ensure_ascii=False)

    print("\n================ TOP 10 PASSAGENS MAIS BARATAS ================")
    for r in resultados[:10]:
        print(f"R$ {r['preco']} | {r['origem']} ➔ {r['destino']} | {r['data_ida']} a {r['data_volta']} ({r['label']}) | {r['cia']} | Horário: {r['horario_ida']}")

if __name__ == "__main__":
    main()
