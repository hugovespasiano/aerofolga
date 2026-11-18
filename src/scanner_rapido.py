import sys
import time
from fast_flights import FlightQuery, Passengers, create_query, get_flights

destinos = ['CWB', 'VIX', 'CNF', 'BSB', 'FLN', 'SSA', 'IGU', 'NVT']
janelas = [
    ('2026-12-22', '2026-12-26', 'Natal 1 (22 a 26/12)'),
    ('2026-12-23', '2026-12-27', 'Natal 2 (23 a 27/12)'),
    ('2026-12-30', '2027-01-03', 'Reveillon 1 (30/12 a 03/01)'),
    ('2026-12-31', '2027-01-04', 'Reveillon 2 (31/12 a 04/01)'),
    ('2027-01-04', '2027-01-08', 'Janeiro 1 (04 a 08/01)'),
    ('2027-01-05', '2027-01-09', 'Janeiro 2 (05 a 09/01)'),
    ('2027-01-06', '2027-01-10', 'Janeiro 3 (06 a 10/01)')
]

achados = []

print("Iniciando varredura rápida de fim de ano...")

for d_ida, d_volta, label in janelas:
    print(f"\n--- {label} ---")
    for dest in destinos:
        for orig in ['GIG', 'GRU']:
            try:
                q = create_query(
                    flights=[
                        FlightQuery(date=d_ida, from_airport=orig, to_airport=dest),
                        FlightQuery(date=d_volta, from_airport=dest, to_airport=orig)
                    ],
                    seat='economy',
                    trip='round-trip',
                    passengers=Passengers(adults=1),
                    currency='BRL',
                    language='pt-BR'
                )
                res = get_flights(q)
                if res:
                    valid = [f for f in res if f.price and f.price > 0]
                    if valid:
                        best = min(valid, key=lambda x: x.price)
                        cia_nome = best.airlines[0] if best.airlines else "Cia"
                        achados.append({
                            'label': label,
                            'origem': orig,
                            'destino': dest,
                            'ida': d_ida,
                            'volta': d_volta,
                            'preco': best.price,
                            'cia': cia_nome,
                            'flights': best.flights
                        })
                        print(f"[{orig} -> {dest}] R$ {best.price} ({cia_nome})")
            except Exception as e:
                # print(f"Erro {orig}->{dest}: {e}")
                pass
            time.sleep(0.15)

print("\n================== TOP 10 ABSOLUTO ==================")
achados.sort(key=lambda x: x['preco'])
for item in achados[:10]:
    print(f"R$ {item['preco']} | {item['origem']} ➔ {item['destino']} | {item['ida']} a {item['volta']} ({item['label']}) | Cia: {item['cia']}")
