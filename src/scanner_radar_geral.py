import json
import concurrent.futures
from fast_flights import FlightQuery, Passengers, create_query, get_flights

janelas_teste = [
    # 1. Férias Janeiro 2027
    ("2027-01-06", "2027-01-10", "Férias Janeiro (06 a 10/01)"),
    ("2027-01-13", "2027-01-17", "Férias Janeiro (13 a 17/01)"),
    # 2. Carnaval 2027
    ("2027-02-05", "2027-02-09", "Carnaval (05 a 09/02)"),
    ("2027-02-06", "2027-02-10", "Carnaval (06 a 10/02)"),
    # 3. Super Feriadão Tiradentes + São Jorge 2027 (21 a 25/04)
    ("2027-04-21", "2027-04-25", "Tiradentes + São Jorge (21 a 25/04)"),
    # 4. Feriado Corpus Christi 2027 (27 a 31/05)
    ("2027-05-27", "2027-05-31", "Corpus Christi (27 a 31/05)"),
    # 5. Baixa Temporada Maio 2027 (Preço Piso de Chão)
    ("2027-05-13", "2027-05-17", "Baixa Temporada Maio (13 a 17/05)")
]

destinos = [
    {"cod": "VIX", "nome": "Vitória (ES)"},
    {"cod": "CWB", "nome": "Curitiba (PR)"},
    {"cod": "CNF", "nome": "Belo Horizonte (MG)"},
    {"cod": "BSB", "nome": "Brasília (DF)"},
    {"cod": "FLN", "nome": "Florianópolis (SC)"},
    {"cod": "SSA", "nome": "Salvador (BA)"}
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
                    "escalas": len(best.flights) - 1
                }
    except Exception:
        pass
    return None

tarefas = []
for ida, volta, label in janelas_teste:
    for d in destinos:
        tarefas.append(("GIG", d, ida, volta, label))

print(f"Disparando {len(tarefas)} buscas no Google Flights...")
achados = []
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(consultar, *t) for t in tarefas]
    for f in concurrent.futures.as_completed(futs):
        r = f.result()
        if r:
            achados.append(r)

achados.sort(key=lambda x: x["preco"])
print("\n=== RANKING DAS PASSAGENS MAIS BARATAS ENCONTRADAS ===")
for item in achados[:15]:
    print(f"R$ {item['preco']:>4} | {item['origem']} -> {item['destino']} ({item['destino_nome']}) | {item['label']} | {item['cia']} | Horario: {item['horario_ida']}")

with open("data/ultimas_passagens_baratas.json", "w", encoding="utf-8") as f:
    json.dump(achados, f, indent=2, ensure_ascii=False)
