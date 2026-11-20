import json
import concurrent.futures
from fast_flights import FlightQuery, Passengers, create_query, get_flights

# Janelas reais de 2027 sincronizadas com os vínculos do Hugo (SEEDUC/Itatiaia/TRE) e Esposa (VR)
janelas_2027 = [
    # 1. Carnaval
    ("2027-02-05", "2027-02-09", "Carnaval (05 a 09/02)", "Feriado Estadual Terça de Carnaval + Ponto Facultativo Segunda"),
    ("2027-02-06", "2027-02-10", "Carnaval (06 a 10/02)", "Sábado a Quarta de Cinzas"),
    # 2. Semana Santa
    ("2027-03-26", "2027-03-28", "Semana Santa (26 a 28/03)", "Sexta-feira da Paixão a Domingo de Páscoa"),
    # 3. Super Feriadão Tiradentes + São Jorge
    ("2027-04-21", "2027-04-25", "Tiradentes + São Jorge (21 a 25/04)", "Quarta a Domingo (Tiradentes 21/04 + São Jorge 23/04 + 1 TRE Hugo)"),
    # 4. Corpus Christi
    ("2027-05-27", "2027-05-31", "Corpus Christi (27 a 31/05)", "Quinta a Segunda (Corpus Christi 27/05 + Ponte/TRE)"),
    # 5. Independência do Brasil
    ("2027-09-03", "2027-09-07", "Independência (03 a 07/09)", "Sexta a Terça (Independência 07/09 na Terça + Ponte Segunda)"),
    # 6. Nossa Senhora Aparecida
    ("2027-10-08", "2027-10-12", "Nossa Sra Aparecida (08 a 12/10)", "Sexta a Terça (Padroeira 12/10 na Terça + Ponte Segunda)"),
    # 7. Finados
    ("2027-10-29", "2027-11-02", "Finados (29/10 a 02/11)", "Sexta a Terça (Finados 02/11 na Terça + Ponte Segunda)"),
    # 8. Proclamação da República
    ("2027-11-12", "2027-11-15", "Proclamação República (12 a 15/11)", "Sexta a Segunda (Proclamação 15/11 na Segunda)")
]

destinos = [
    ("CWB", "Curitiba (PR)"),
    ("VIX", "Vitória (ES)"),
    ("CNF", "Belo Horizonte (MG)"),
    ("BSB", "Brasília (DF)"),
    ("FLN", "Florianópolis (SC)"),
    ("SSA", "Salvador (BA)")
]

def consultar(orig, dest, d_nome, ida, volta, label, motivo):
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
                    "ida": ida, "volta": volta, "label": label, "motivo": motivo,
                    "preco": b.price, "cia": cia, "horario_ida": h_ida,
                    "url": f"https://www.google.com/travel/flights?q=Flights%20to%20{dest}%20from%20{orig}%20on%20{ida}%20through%20{volta}"
                }
    except Exception:
        pass
    return None

tarefas = []
for ida, volta, label, motivo in janelas_2027:
    for dest, d_nome in destinos:
        tarefas.append(("GIG", dest, d_nome, ida, volta, label, motivo))

print(f"Disparando {len(tarefas)} consultas para todas as folgas e feriados de 2027...")
achados = []
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(consultar, *t) for t in tarefas]
    for f in concurrent.futures.as_completed(futs):
        r = f.result()
        if r:
            achados.append(r)

achados.sort(key=lambda x: x["preco"])
print("\n=== RANKING DAS PASSAGENS MAIS BARATAS DE 2027 EM FOLGAS/FERIADOS ===")
for item in achados[:15]:
    print(f"R$ {item['preco']:>4} | {item['origem']} ➔ {item['destino']} ({item['destino_nome']}) | {item['label']} | {item['cia']} | Horário: {item['horario_ida']}")

import os
os.makedirs("data", exist_ok=True)
with open("data/varredura_feriados_2027.json", "w", encoding="utf-8") as f:
    json.dump(achados, f, indent=2, ensure_ascii=False)
