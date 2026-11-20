import json
import concurrent.futures
from fast_flights import FlightQuery, Passengers, create_query, get_flights

# Testando fins de semana normais e baixa temporada (Maio, Junho, Agosto, Setembro 2027)
# Rota curta: Rio (GIG/SDU) para SP (CGH/GRU), BH (CNF), Vitoria (VIX), Curitiba (CWB)
amostras = [
    # Maio 2027 (baixa temporada clássica)
    ("2027-05-07", "2027-05-10", "GIG", "VIX", "Maio (07 a 10/05)"),
    ("2027-05-14", "2027-05-17", "GIG", "CNF", "Maio (14 a 17/05)"),
    ("2027-05-14", "2027-05-17", "GIG", "CWB", "Maio (14 a 17/05)"),
    ("2027-05-21", "2027-05-24", "SDU", "CGH", "Maio Ponte (21 a 24/05)"),
    ("2027-05-21", "2027-05-24", "GIG", "GRU", "Maio Rio-SP (21 a 24/05)"),
    # Junho 2027
    ("2027-06-04", "2027-06-07", "GIG", "VIX", "Junho (04 a 07/06)"),
    ("2027-06-11", "2027-06-14", "GIG", "CNF", "Junho (11 a 14/06)"),
    ("2027-06-18", "2027-06-21", "GIG", "CWB", "Junho (18 a 21/06)"),
    # Agosto 2027
    ("2027-08-13", "2027-08-16", "GIG", "VIX", "Agosto (13 a 16/08)"),
    ("2027-08-20", "2027-08-23", "GIG", "CNF", "Agosto (20 a 23/08)"),
    ("2027-08-20", "2027-08-23", "GIG", "CWB", "Agosto (20 a 23/08)")
]

def buscar(ida, volta, orig, dest, label):
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
                    h_ida = f"{f0.departure.time[0]:02d}:{f0.departure.time[1]:02d}"
                tarifa_pess = float(b.price)
                custo_log = 350.0 if orig in ("GIG", "SDU") else 760.0
                total_casal = (tarifa_pess * 2) + custo_log
                return {
                    "origem": orig, "destino": dest, "ida": ida, "volta": volta,
                    "label": label, "preco": tarifa_pess, "total_casal": total_casal,
                    "cia": cia, "horario": h_ida
                }
    except Exception:
        pass
    return None

print("Testando pisos históricos de baixa temporada em fins de semana normais...")
achados = []
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(buscar, *a) for a in amostras]
    for f in concurrent.futures.as_completed(futs):
        r = f.result()
        if r:
            achados.append(r)

achados.sort(key=lambda x: x["preco"])
print("\n=== RESULTADOS DE PISO REAL DE BAIXA TEMPORADA ===")
for item in achados:
    print(f"R$ {item['preco']:>3.0f} /pessoa (Ida+Volta) | Total Casal Porta a Porta: R$ {item['total_casal']:>6.2f} | {item['origem']} ➔ {item['destino']} | {item['label']} | {item['cia']}")
