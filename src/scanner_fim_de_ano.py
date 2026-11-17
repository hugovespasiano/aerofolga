"""
scanner_fim_de_ano.py — AeroFolga / Vespasiano Labs
Varredura real no Google Flights para a janela de Fim de Ano e Férias Escolares:
20 de Dezembro a 10 de Janeiro.
Origens: Rio de Janeiro (GIG/SDU) e São Paulo (GRU/VCP/CGH).
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from fast_flights import FlightQuery, Passengers, create_query, get_flights

DESTINOS = [
    {"codigo": "VIX", "nome": "Vitória (ES)", "regiao": "Sudeste"},
    {"codigo": "CWB", "nome": "Curitiba (PR)", "regiao": "Sul"},
    {"codigo": "CNF", "nome": "Belo Horizonte (MG)", "regiao": "Sudeste"},
    {"codigo": "BSB", "nome": "Brasília (DF)", "regiao": "Centro-Oeste"},
    {"codigo": "FLN", "nome": "Florianópolis (SC)", "regiao": "Sul"},
    {"codigo": "SSA", "nome": "Salvador (BA)", "regiao": "Nordeste"},
    {"codigo": "BPS", "nome": "Porto Seguro (BA)", "regiao": "Nordeste"},
    {"codigo": "REC", "nome": "Recife (PE)", "regiao": "Nordeste"}
]

JANELAS = [
    {"ida": "2026-12-22", "volta": "2026-12-28", "nome": "Semana do Natal (22/12 a 28/12)"},
    {"ida": "2026-12-28", "volta": "2027-01-03", "nome": "Réveillon (28/12 a 03/01)"},
    {"ida": "2027-01-04", "volta": "2027-01-10", "nome": "Pós-Réveillon / Desova de Janeiro (04/01 a 10/01)"}
]


def consultar_rota(origem: str, destino: str, data_ida: str, data_volta: str) -> List[Dict[str, Any]]:
    try:
        query = create_query(
            flights=[
                FlightQuery(date=data_ida, from_airport=origem, to_airport=destino),
                FlightQuery(date=data_volta, from_airport=destino, to_airport=origem)
            ],
            seat="economy",
            trip="round-trip",
            passengers=Passengers(adults=1),
            currency="BRL",
            language="pt-BR"
        )
        res = get_flights(query)
        if not res or len(res) == 0:
            return []

        resultados = []
        for f in res:
            if not f.price:
                continue
            tem_conexao = len(f.flights) > 1
            duracao_total = sum(leg.duration for leg in f.flights) if hasattr(f, "flights") else 0

            url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destino}%20from%20{origem}%20on%20{data_ida}%20through%20{data_volta}"

            resultados.append({
                "origem": origem,
                "destino": destino,
                "data_ida": data_ida,
                "data_volta": data_volta,
                "preco": f.price,
                "companhias": f.airlines,
                "voo_direto": not tem_conexao,
                "conexoes": len(f.flights) - 1 if tem_conexao else 0,
                "duracao_minutos": duracao_total,
                "url": url
            })
        return resultados
    except Exception as e:
        # print(f"Erro: {e}")
        return []


def executar_varredura():
    print("==================================================================")
    print("✈️  AEROFOLGA — SCANNER REAL GOOGLE FLIGHTS (FIM DE ANO / FÉRIAS)")
    print("    Período Solicitado: 20 de Dezembro a 10 de Janeiro")
    print("    Origens: Rio de Janeiro (GIG/SDU) e SP (GRU/CGH/VCP)")
    print("==================================================================\n")

    todos_achados = []

    for janela in JANELAS:
        print(f"\n🔍 [Janela] {janela['nome']}")
        print("-" * 60)

        for dest in DESTINOS:
            # 1. Preferência principal: Rio de Janeiro (GIG)
            origens_para_testar = [("GIG", "Rio (GIG)")]
            
            # 2. Alternativa SP para rotas competitivas
            if dest["codigo"] in ["CWB", "FLN", "SSA", "VIX"]:
                origens_para_testar.append(("GRU", "São Paulo (GRU)"))

            for aeroporto, label in origens_para_testar:
                print(f"   -> {label} ⇄ {dest['codigo']} ({dest['nome']})... ", end="", flush=True)
                achados = consultar_rota(aeroporto, dest["codigo"], janela["ida"], janela["volta"])
                
                if achados:
                    melhor = min(achados, key=lambda x: x["preco"])
                    melhor["destino_nome"] = dest["nome"]
                    melhor["regiao"] = dest["regiao"]
                    melhor["janela_nome"] = janela["nome"]
                    todos_achados.append(melhor)
                    direto_txt = "Direto" if melhor["voo_direto"] else f"{melhor['conexoes']} escala(s)"
                    print(f"Encontrado: R$ {melhor['preco']} ({', '.join(melhor['companhias'])} | {direto_txt})")
                else:
                    print("Sem disponibilidade promocional.")
                
                time.sleep(0.3)

    print("\n" + "=" * 66)
    print("🏆 TOP VOOS MAIS BARATOS ENCONTRADOS NO PERÍODO")
    print("=" * 66)

    todos_achados.sort(key=lambda x: x["preco"])

    for i, voo in enumerate(todos_achados[:10], 1):
        tipo_voo = "Voo Direto" if voo["voo_direto"] else f"{voo['conexoes']} escala(s)"
        print(f"\n[{i}] {voo['origem']} ⇄ {voo['destino']} ({voo['destino_nome']}) — R$ {voo['preco']} (Ida e Volta)")
        print(f"    📅 Datas: {voo['data_ida']} a {voo['data_volta']} | {voo['janela_nome']}")
        print(f"    🛫 Companhia: {', '.join(voo['companhias'])} | {tipo_voo}")
        print(f"    🔗 Reserva Google Flights: {voo['url']}")

if __name__ == "__main__":
    executar_varredura()
