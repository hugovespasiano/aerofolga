"""
mega_scanner_2027.py — AeroFolga / Vespasiano Labs
Varredura exaustiva ao vivo para o ano inteiro de 2027:
- Feriados Nacionais, Estaduais (RJ), Municipais (VR/Itatiaia/BM)
- Pontos Facultativos e Enforcamentos com Folga TRE
- Compara Galeão (GIG), Congonhas (CGH) e Guarulhos (GRU) lado a lado
- Elege o melhor custo Porta a Porta do Casal
"""

import sys
import json
import time
import concurrent.futures
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from fast_flights import FlightQuery, Passengers, create_query, get_flights
from notifier.disparador import DisparadorAlerta
from notifier.formatador_alerta import formatar_alerta_novo_padrao, sugerir_horario_onibus

# Todos os feriadões e janelas de folga sincronizados para Hugo e Esposa em 2027
JANELAS_2027 = [
    # 1. Carnaval
    ("2027-02-05", "2027-02-09", "Carnaval (05 a 09/02)", "Feriado Terça + Ponto Facultativo Segunda"),
    ("2027-02-06", "2027-02-10", "Carnaval (06 a 10/02)", "Sábado a Quarta de Cinzas"),
    # 2. Semana Santa / Páscoa
    ("2027-03-26", "2027-03-28", "Semana Santa (26 a 28/03)", "Sexta-feira da Paixão a Domingo"),
    # 3. Super Feriadão de Abril (Tiradentes + São Jorge)
    ("2027-04-21", "2027-04-25", "Tiradentes + São Jorge (21 a 25/04)", "Quarta a Domingo (Tiradentes 21/04 + 1 TRE Hugo + São Jorge 23/04)"),
    # 4. Corpus Christi
    ("2027-05-27", "2027-05-31", "Corpus Christi (27 a 31/05)", "Quinta a Segunda (Corpus Christi 27/05 + Ponte Sexta 28/05)"),
    # 5. Férias de Meio de Ano / Recesso Escolar
    ("2027-07-17", "2027-07-21", "Férias de Julho (17 a 21/07)", "Emancipação de Volta Redonda 17/07 + Recesso de Meio de Ano"),
    # 6. Independência do Brasil
    ("2027-09-03", "2027-09-07", "Independência (03 a 07/09)", "Sexta a Terça (Independência 07/09 na Terça + Ponte Segunda 06/09)"),
    # 7. Nossa Senhora Aparecida
    ("2027-10-08", "2027-10-12", "Nossa Sra Aparecida (08 a 12/10)", "Sexta a Terça (Padroeira 12/10 na Terça + Ponte Segunda 11/10)"),
    # 8. Finados
    ("2027-10-29", "2027-11-02", "Finados (29/10 a 02/11)", "Sexta a Terça (Finados 02/11 na Terça + Ponte Segunda 01/11)"),
    # 9. Proclamação da República
    ("2027-11-12", "2027-11-15", "Proclamação República (12 a 15/11)", "Sexta a Segunda (Proclamação 15/11 na Segunda)")
]

DESTINOS = [
    ("CWB", "Curitiba (PR)"),
    ("VIX", "Vitória (ES)"),
    ("FLN", "Florianópolis (SC)"),
    ("CNF", "Belo Horizonte (MG)"),
    ("BSB", "Brasília (DF)"),
    ("NVT", "Navegantes (SC)"),
    ("SSA", "Salvador (BA)"),
    ("IGU", "Foz do Iguaçu (PR)")
]

ORIGENS = [
    ("GIG", "Rio de Janeiro (Galeão)", 350.0),
    ("CGH", "São Paulo (Congonhas)", 730.0),
    ("GRU", "São Paulo (Guarulhos)", 760.0)
]

def consultar_rota(orig, orig_nome, custo_log, dest, dest_nome, ida, volta, label, motivo):
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

                tarifa_pessoa = float(b.price)
                passagens_casal = tarifa_pessoa * 2
                custo_total_casal = passagens_casal + custo_log

                return {
                    "origem": orig,
                    "origem_nome": orig_nome,
                    "custo_logistica": custo_log,
                    "destino": dest,
                    "destino_nome": dest_nome,
                    "ida": ida,
                    "volta": volta,
                    "label": label,
                    "motivo": motivo,
                    "tarifa_pessoa": tarifa_pessoa,
                    "passagens_casal": passagens_casal,
                    "custo_total_casal": custo_total_casal,
                    "cia": cia,
                    "horario_ida": h_ida,
                    "url": f"https://www.google.com/travel/flights?q=Flights%20to%20{dest}%20from%20{orig}%20on%20{ida}%20through%20{volta}"
                }
    except Exception:
        pass
    return None

def main():
    tarefas = []
    for ida, volta, label, motivo in JANELAS_2027:
        for dest, dest_nome in DESTINOS:
            for orig, orig_nome, custo_log in ORIGENS:
                tarefas.append((orig, orig_nome, custo_log, dest, dest_nome, ida, volta, label, motivo))

    print(f"🚀 Iniciando Super Varredura de 2027: {len(tarefas)} buscas em paralelo (GIG vs CGH vs GRU)...")
    achados = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futs = [executor.submit(consultar_rota, *t) for t in tarefas]
        for f in concurrent.futures.as_completed(futs):
            res = f.result()
            if res:
                achados.append(res)

    # Ordena pelo menor custo final real do casal (Passagens + Logística VR)
    achados.sort(key=lambda x: x["custo_total_casal"])

    print(f"\n✅ Total de rotas capturadas: {len(achados)}")
    print("\n🏆 TOP 15 MELHORES VIAGENS DE 2027 (PORTA A PORTA CASAL):")
    for a in achados[:15]:
        print(f"R$ {a['custo_total_casal']:>7.2f} CASAL | {a['origem']} ➔ {a['destino']} ({a['destino_nome']}) | R$ {a['tarifa_pessoa']:.0f}/pess | {a['label']} | {a['cia']}")

    # Salva os resultados completos
    with open("data/todas_viagens_2027.json", "w", encoding="utf-8") as f:
        json.dump(achados, f, indent=2, ensure_ascii=False)

    # Dispara os 3 campeões absolutos de 2027 para o Telegram
    disp = DisparadorAlerta()
    print("\n📲 Disparando os 3 maiores campeões de 2027 para o Telegram...")

    # Garante que sejam 3 janelas diferentes (ex: Tiradentes, Corpus Christi, Carnaval)
    disparados = []
    janelas_vistas = set()
    for a in achados:
        if a["label"] not in janelas_vistas and len(disparados) < 3:
            janelas_vistas.add(a["label"])
            disparados.append(a)

    for v in disparados:
        detalhe_onibus = sugerir_horario_onibus(v["horario_ida"], v["origem"])
        selo_origem = f"🏆 Vencedor: {v['origem_nome']} ({v['cia']})"

        msg = formatar_alerta_novo_padrao(
            origem=v["origem"],
            origem_nome=v["origem_nome"],
            destino=v["destino"],
            destino_nome=v["destino_nome"],
            datas_label=f"{v['ida']} a {v['volta']} ({v['label']})",
            tarifa_pessoa=float(v["tarifa_pessoa"]),
            cia_aerea=v["cia"],
            horario_ida=v["horario_ida"] or "Opções diretas",
            horario_volta="Conforme opções do pacote",
            onibus_detalhe=detalhe_onibus,
            url_reserva=v["url"],
            modo="html"
        )
        msg_telegram = f"🗓️ <b>PLANEJAMENTO ANUAL 2027 — MELHOR OPÇÃO DE FERIADÃO</b>\n" + msg
        disp.enviar_telegram(msg_telegram)
        time.sleep(1)

    print("🎉 Disparos concluídos com sucesso!")

if __name__ == "__main__":
    main()
