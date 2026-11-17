import re
from fast_flights import FlightQuery, Passengers, create_query
from fast_flights.fetcher import fetch_flights_html

query = create_query(
    flights=[
        FlightQuery(date='2026-12-30', from_airport='GIG', to_airport='CWB'),
        FlightQuery(date='2027-01-03', from_airport='CWB', to_airport='GIG')
    ],
    seat='economy',
    trip='round-trip',
    passengers=Passengers(adults=1),
    currency='BRL',
    language='pt-BR'
)

html = fetch_flights_html(query)

# 1. Extração por regex de todas as declarações de preço real do Google Flights: [[null, PRECO], "Cj...
matches = re.findall(r'\[\[null,(\d{3,5})\],"(?:Cj|[A-Za-z0-9_-])', html)
precos = [int(p) for p in matches]

print("Preços identificados no payload:", precos)
if precos:
    menor_real = min(precos)
    print(f"✅ MENOR PREÇO REAL ENCONTRADO: R$ {menor_real}")
