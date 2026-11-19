import json
import concurrent.futures
from fast_flights import FlightQuery, Passengers, create_query, get_flights

# Gera janelas de 3 a 5 noites entre 20/12/2026 e 10/01/2027
janelas = [
    # Semana Pré-Natal / Natal
    ("2026-12-21", "2026-12-25", "Natal (21 a 25/12)"),
    ("2026-12-22", "2026-12-26", "Natal (22 a 26/12)"),
    ("2026-12-23", "2026-12-27", "Natal (23 a 27/12)"),
    ("2026-12-24", "2026-12-28", "Natal (24 a 28/12)"),
    # Entre Natal e Ano Novo
    ("2026-12-26", "2026-12-30", "Fim de Ano (26 a 30/12)"),
    ("2026-12-27", "2026-12-31", "Fim de Ano (27 a 31/12)"),
    # Réveillon (Virada de Ano)
    ("2026-12-29", "2027-01-02", "Réveillon (29/12 a 02/01)"),
    ("2026-12-30", "2027-01-03", "Réveillon (30/12 a 03/01)"),
    ("2026-12-31", "2027-01-04", "Réveillon (31/12 a 04/01)"),
    # Pós-Réveillon / Férias de Janeiro
    ("2027-01-02", "2027-01-06", "Janeiro (02 a 06/01)"),
    ("2027-01-03", "2027-01-07", "Janeiro (03 a 07/01)"),
    ("2027-01-04", "2027-01-08", "Janeiro (04 a 08/01)"),
    ("2027-01-05", "2027-01-09", "Janeiro (05 a 09/01)"),
    ("2027-01-06", "2027-01-10", "Janeiro (06 a 10/01)")
]

destinos = [
    {"cod": "VIX", "nome": "Vitória (ES)"},
    {"cod": "CWB", "nome": "Curitiba (PR)"},
    {"cod": "CNF", "nome": "Belo Horizonte (MG)"},
    {"cod": "BSB", "nome": "Brasília (DF)"},
    {"cod": "FLN", "nome": "Florianópolis (SC)"},
    {"cod": "SSA", "nome": "Salvador (BA)"},
    {"cod": "NVT", "nome": "Navegantes (SC)"},
    {"cod": "IGU", "nome": "Foz do Iguaçu (PR)"}
]

def consultar(orig, dest_info, ida, volta, label):
    dest = dest_info["cod"]
    try:
        q = create_query(
            flights=[
                FlightQuery(date=ida, from_airport=orig, to_airport=dest),
                FlightQuery(date=volta, from_airport=dest, to_airport=orig)
            ],
            seat="economy",
            trip="round-trip",
            passengers=Passengers(adults=1),
            currency="BRL",
            language="pt-BR"
        )
        res = get_flights(q)
        if res:
            valid = [f for f in res if f.price and f.price > 0]
            if valid:
                best = min(valid, key=lambda x: x.price)
                cia = best.airlines[0] if best.airlines else "Cia"
                h_ida = ""
                if best.flights:
                    f0 = best.flights[0]
                    h_ida = f"{f0.departure.time[0]:02d}:{f0.departure.time[1]:02d} -> {f0.arrival.time[0]:02d}:{f0.arrival.time[1]:02d}"
                return {
                    "origem": orig,
                    "destino": dest,
                    "destino_nome": dest_info["nome"],
                    "ida": ida,
                    "volta": volta,
                    "label": label,
                    "preco": best.price,
                    "cia": cia,
                    "horario_ida": h_ida,
                    "escalas": len(best.flights) - 1,
                    "url": f"https://www.google.com/travel/flights?q=Flights%20to%20{dest}%20from%20{orig}%20on%20{ida}%20through%20{volta}"
                }
    except Exception:
        pass
    return None

tarefas = []
for ida, volta, label in janelas:
    for d in destinos:
        tarefas.append(("GIG", d, ida, volta, label))

print(f"Varrendo {len(tarefas)} combinações reais entre 20/12/2026 e 10/01/2027...")
achados = []
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(consultar, *t) for t in tarefas]
    for f in concurrent.futures.as_completed(futs):
        r = f.result()
        if r:
            achados.append(r)

achados.sort(key=lambda x: x["preco"])
print("\n=== RANKING DAS 10 TARIFAS MAIS BARATAS DO PERÍODO ===")
for item in achados[:10]:
    print(f"R$ {item['preco']:>4} | {item['origem']} -> {item['destino']} ({item['destino_nome']}) | {item['label']} | {item['cia']} | Horario: {item['horario_ida']}")

import os
os.makedirs("data", exist_ok=True)
with open("data/varredura_20dez_10jan.json", "w", encoding="utf-8") as f:
    json.dump(achados, f, indent=2, ensure_ascii=False)
