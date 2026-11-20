import json
import concurrent.futures
from fast_flights import FlightQuery, Passengers, create_query, get_flights

janelas = [
    # Natal
    ("2026-12-21", "2026-12-25", "Natal (21 a 25/12)"),
    ("2026-12-22", "2026-12-26", "Natal (22 a 26/12)"),
    ("2026-12-23", "2026-12-27", "Natal (23 a 27/12)"),
    ("2026-12-24", "2026-12-28", "Natal (24 a 28/12)"),
    # Entre Natal e Réveillon
    ("2026-12-26", "2026-12-30", "Fim de Ano (26 a 30/12)"),
    ("2026-12-27", "2026-12-31", "Fim de Ano (27 a 31/12)"),
    # Réveillon
    ("2026-12-29", "2027-01-02", "Réveillon (29/12 a 02/01)"),
    ("2026-12-30", "2027-01-03", "Réveillon (30/12 a 03/01)"),
    ("2026-12-31", "2027-01-04", "Réveillon (31/12 a 04/01)"),
    # Janeiro
    ("2027-01-03", "2027-01-07", "Janeiro (03 a 07/01)"),
    ("2027-01-04", "2027-01-08", "Janeiro (04 a 08/01)"),
    ("2027-01-05", "2027-01-09", "Janeiro (05 a 09/01)"),
    ("2027-01-06", "2027-01-10", "Janeiro (06 a 10/01)")
]

destinos = [
    ("VIX", "Vitória (ES)"),
    ("CWB", "Curitiba (PR)"),
    ("CNF", "Belo Horizonte (MG)"),
    ("BSB", "Brasília (DF)"),
    ("FLN", "Florianópolis (SC)"),
    ("SSA", "Salvador (BA)"),
    ("IGU", "Foz do Iguaçu (PR)"),
    ("NVT", "Navegantes (SC)")
]

def buscar(orig, dest, d_nome, ida, volta, label):
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
                b = min(valid, key=lambda x: x.price)
                cia = b.airlines[0] if b.airlines else "Cia"
                h_ida = ""
                if b.flights:
                    f0 = b.flights[0]
                    h_ida = f"{f0.departure.time[0]:02d}:{f0.departure.time[1]:02d} ➔ {f0.arrival.time[0]:02d}:{f0.arrival.time[1]:02d}"
                return {
                    "origem": orig, "destino": dest, "destino_nome": d_nome,
                    "ida": ida, "volta": volta, "label": label,
                    "preco": b.price, "cia": cia, "horario_ida": h_ida,
                    "url": f"https://www.google.com/travel/flights?q=Flights%20to%20{dest}%20from%20{orig}%20on%20{ida}%20through%20{volta}"
                }
    except Exception:
        pass
    return None

tarefas = []
for ida, volta, label in janelas:
    for dest, d_nome in destinos:
        tarefas.append(("GIG", dest, d_nome, ida, volta, label))

print(f"Varrendo {len(tarefas)} rotas ao vivo no Google Voos...")
achados = []
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(buscar, *t) for t in tarefas]
    for f in concurrent.futures.as_completed(futs):
        r = f.result()
        if r:
            achados.append(r)

achados.sort(key=lambda x: x["preco"])
print("\n=== TOP 12 MENORES PREÇOS (20/12 A 10/01) ===")
for item in achados[:12]:
    print(f"R$ {item['preco']:>4} | {item['origem']} -> {item['destino']} ({item['destino_nome']}) | {item['label']} | {item['cia']} | Horario: {item['horario_ida']}")

with open("data/pesquisa_recente_dez_jan.json", "w", encoding="utf-8") as f:
    json.dump(achados, f, indent=2, ensure_ascii=False)
