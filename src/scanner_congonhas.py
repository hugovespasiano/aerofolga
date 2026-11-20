import json
import concurrent.futures
from fast_flights import FlightQuery, Passengers, create_query, get_flights

janelas = [
    ("2026-12-21", "2026-12-25", "Natal (21 a 25/12)"),
    ("2026-12-23", "2026-12-27", "Natal (23 a 27/12)"),
    ("2026-12-29", "2027-01-02", "Réveillon (29/12 a 02/01)"),
    ("2026-12-30", "2027-01-03", "Réveillon (30/12 a 03/01)"),
    ("2026-12-31", "2027-01-04", "Réveillon (31/12 a 04/01)"),
    ("2027-01-04", "2027-01-08", "Janeiro (04 a 08/01)"),
    ("2027-01-06", "2027-01-10", "Janeiro (06 a 10/01)")
]

destinos = [
    ("CWB", "Curitiba (PR)"),
    ("FLN", "Florianópolis (SC)"),
    ("NVT", "Navegantes (SC)"),
    ("IGU", "Foz do Iguaçu (PR)"),
    ("VIX", "Vitória (ES)"),
    ("SSA", "Salvador (BA)"),
    ("CNF", "Belo Horizonte (MG)")
]

# Logística VR ➔ CGH: Cometa R$ 620 + Uber Tietê/CGH R$ 110 = R$ 730 casal
custo_log_cgh = 730.0

def consultar_cgh(dest, dest_nome, ida, volta, label):
    try:
        q = create_query(
            flights=[
                FlightQuery(date=ida, from_airport="CGH", to_airport=dest),
                FlightQuery(date=volta, from_airport=dest, to_airport="CGH")
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

                tarifa_pessoa = float(b.price)
                passagens_casal = tarifa_pessoa * 2
                custo_total_casal = passagens_casal + custo_log_cgh

                return {
                    "origem": "CGH",
                    "origem_nome": "São Paulo (Congonhas)",
                    "destino": dest,
                    "destino_nome": dest_nome,
                    "ida": ida,
                    "volta": volta,
                    "label": label,
                    "tarifa_pessoa": tarifa_pessoa,
                    "passagens_casal": passagens_casal,
                    "custo_total_casal": custo_total_casal,
                    "cia": cia,
                    "horario_ida": h_ida,
                    "url": f"https://www.google.com/travel/flights?q=Flights%20to%20{dest}%20from%20CGH%20on%20{ida}%20through%20{volta}"
                }
    except Exception:
        pass
    return None

tarefas = []
for ida, volta, label in janelas:
    for dest, dest_nome in destinos:
        tarefas.append((dest, dest_nome, ida, volta, label))

print(f"Varrendo Congonhas (CGH): {len(tarefas)} buscas...")
achados = []
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(consultar_cgh, *t) for t in tarefas]
    for f in concurrent.futures.as_completed(futs):
        r = f.result()
        if r:
            achados.append(r)

achados.sort(key=lambda x: x["custo_total_casal"])

print("\n=== TOP 10 MENORES PREÇOS SAINDO DE CONGONHAS (PORTA A PORTA CASAL) ===")
for item in achados[:10]:
    print(f"R$ {item['custo_total_casal']:>7.2f} CASAL | CGH ➔ {item['destino']} | R$ {item['tarifa_pessoa']:.0f}/pess | {item['label']} | {item['cia']} | Horário: {item['horario_ida']}")

with open("data/varredura_congonhas.json", "w", encoding="utf-8") as f:
    json.dump(achados, f, indent=2, ensure_ascii=False)
