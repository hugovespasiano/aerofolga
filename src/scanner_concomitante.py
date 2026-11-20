"""
scanner_concomitante.py — AeroFolga / Vespasiano Labs
Varredura Concomitante:
1. Janelas 100% PURAS (Feriados Nacionais, Estaduais RJ, Municipais e Pontos Facultativos Tradicionais - 0 folgas TRE)
2. Janelas ALAVANCADAS com TRE (Extensões de feriados em 1 ou 2 dias e fins de semana atípicos)
NADA É ABANDONADO: Ambas as estratégias operam lado a lado.
"""

import sys
import time
import json
import concurrent.futures
from pathlib import Path
from datetime import date

sys.path.append(str(Path(__file__).parent))

from fast_flights import FlightQuery, Passengers, create_query, get_flights
from calendar_engine.motor_calendario_unificado import obter_janelas_unificadas_ano, JanelaUnificada
from notifier.formatador_alerta import formatar_alerta_novo_padrao, sugerir_horario_onibus
from notifier.disparador import DisparadorAlerta


DESTINOS = [
    {"cod": "VIX", "nome": "Vitória (ES)"},
    {"cod": "CWB", "nome": "Curitiba (PR)"},
    {"cod": "CNF", "nome": "Belo Horizonte (MG)"},
    {"cod": "BSB", "nome": "Brasília (DF)"},
    {"cod": "FLN", "nome": "Florianópolis (SC)"},
    {"cod": "NVT", "nome": "Navegantes (SC)"},
    {"cod": "IGU", "nome": "Foz do Iguaçu (PR)"},
    {"cod": "SSA", "nome": "Salvador (BA)"}
]


def consultar_voo(orig: str, dest_info: dict, janela: JanelaUnificada):
    dest = dest_info["cod"]
    d_ida = janela.inicio_iso
    d_volta = janela.fim_iso

    try:
        q = create_query(
            flights=[
                FlightQuery(date=d_ida, from_airport=orig, to_airport=dest),
                FlightQuery(date=d_volta, from_airport=dest, to_airport=orig)
            ],
            seat="economy",
            trip="round-trip",
            passengers=Passengers(adults=1),
            currency="BRL",
            language="pt-BR"
        )
        res = get_flights(q)
        if not res:
            return None
        valid = [f for f in res if f.price and f.price > 0]
        if not valid:
            return None

        melhor = min(valid, key=lambda x: x.price)
        cia = melhor.airlines[0] if melhor.airlines else "Cia Aérea"

        h_ida = ""
        if melhor.flights:
            f0 = melhor.flights[0]
            dep_t = f"{f0.departure.time[0]:02d}:{f0.departure.time[1]:02d}"
            arr_t = f"{f0.arrival.time[0]:02d}:{f0.arrival.time[1]:02d}"
            h_ida = f"{dep_t} ➔ {arr_t}"

        if orig in ("GIG", "SDU"):
            custo_log = 350.0
            orig_nome = "Rio de Janeiro (Galeão)"
        elif orig == "CGH":
            custo_log = 730.0
            orig_nome = "São Paulo (Congonhas)"
        elif orig == "GRU":
            custo_log = 760.0
            orig_nome = "São Paulo (Guarulhos)"
        else:
            custo_log = 1110.0
            orig_nome = orig

        custo_casal_total = (melhor.price * 2) + custo_log
        url = f"https://www.google.com/travel/flights?q=Flights%20to%20{dest}%20from%20{orig}%20on%20{d_ida}%20through%20{d_volta}"

        alav_str = None
        if janela.folgas_tre_gastas > 0:
            alav_str = f"Usa {janela.folgas_tre_gastas} folga(s) TRE ({', '.join(janela.dias_tre)}) — {janela.detalhes}"

        return {
            "origem": orig,
            "origem_nome": orig_nome,
            "destino": dest,
            "destino_nome": dest_info["nome"],
            "data_ida": d_ida,
            "data_volta": d_volta,
            "nome_evento": janela.nome_evento,
            "categoria": janela.categoria,
            "folgas_tre_gastas": janela.folgas_tre_gastas,
            "dias_tre": janela.dias_tre,
            "alavancagem_tre": alav_str,
            "tarifa_pessoa": melhor.price,
            "custo_casal_total": custo_casal_total,
            "cia": cia,
            "horario_ida": h_ida,
            "horario_volta": "Conforme opções do pacote",
            "url": url
        }
    except Exception:
        return None


def rodar_varredura_concomitante(disparar_telegram: bool = True):
    print("🚀 Iniciando Varredura Concomitante (Puros + TRE)...")
    todas = obter_janelas_unificadas_ano(2027)

    # 1. Seleciona janelas PURAS prioritárias de feriados e pontos facultativos
    puras_prioritarias = [
        j for j in todas if j.folgas_tre_gastas == 0 and j.nome_evento in (
            "Mega Feriado RJ Tiradentes + São Jorge (Qua ➔ Dom)",
            "Corpus Christi (Ponte Pura com Ponto Facultativo)",
            "Independência do Brasil (Ponte Pura Sáb ➔ Ter)",
            "Nossa Senhora Aparecida (Padroeira do Brasil) (Ponte Pura Sáb ➔ Ter)",
            "Finados (Ponte Pura Sáb ➔ Ter)",
            "Proclamação da República (Feriadão Puro Sáb ➔ Seg)",
            "Sexta-feira Santa (Paixão de Cristo) (Feriadão Puro)"
        )
    ]

    # 2. Concomitantemente, seleciona janelas ALAVANCADAS com TRE
    alavancadas_prioritarias = [
        j for j in todas if j.folgas_tre_gastas > 0 and (
            "Estendido" in j.nome_evento or "Super Ponte" in j.nome_evento or
            (j.inicio.month in (3, 5, 8, 10) and "Sábado a Terça" in j.detalhes)
        )
    ][:6]

    janelas_alvo = puras_prioritarias + alavancadas_prioritarias
    print(f"Janelas selecionadas: {len(janelas_alvo)} ({len(puras_prioritarias)} Puras + {len(alavancadas_prioritarias)} TRE)")

    tarefas = []
    destinos_curtos = [d for d in DESTINOS if d["cod"] in ("VIX", "CWB", "CNF", "FLN", "NVT")]
    for j in janelas_alvo:
        for dest in destinos_curtos:
            tarefas.append(("GIG", dest, j))
            tarefas.append(("CGH", dest, j))

    print(f"Executando {len(tarefas)} consultas reais...")
    encontrados = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futs = [executor.submit(consultar_voo, *t) for t in tarefas]
        for f in concurrent.futures.as_completed(futs):
            res = f.result()
            if res:
                encontrados.append(res)

    print(f"Varredura concluída! {len(encontrados)} voos encontrados.")

    # Carrega tabela de referência
    ref_path = Path(__file__).parent.parent / "data" / "tabela_referencia.json"
    ref_map = {}
    if ref_path.exists():
        with open(ref_path, "r", encoding="utf-8") as rf:
            ref_map = json.load(rf)

    for item in encontrados:
        ref = ref_map.get(item["destino"], {})
        preco_medio = float(ref.get("preco_medio_tipico", 1000.0))
        item["desconto_pct"] = int(round(((preco_medio - item["tarifa_pessoa"]) / preco_medio) * 100))
        item["economia_casal"] = (preco_medio - item["tarifa_pessoa"]) * 2

    # Separa os melhores de cada categoria
    achados_puros = [x for x in encontrados if x["folgas_tre_gastas"] == 0]
    achados_tre = [x for x in encontrados if x["folgas_tre_gastas"] > 0]

    achados_puros.sort(key=lambda x: x["custo_casal_total"])
    achados_tre.sort(key=lambda x: x["custo_casal_total"])

    print("\n🟢 === TOP 3 ACHADOS EM FERIADOS E PONTOS FACULTATIVOS 100% PUROS (0 TRE) ===")
    for idx, d in enumerate(achados_puros[:3], 1):
        print(f"#{idx} | {d['destino']} via {d['origem']} | {d['data_ida']} a {d['data_volta']} ({d['nome_evento']})")
        print(f"    Tarifa: R$ {d['tarifa_pessoa']:.2f}/pessoa | Casal Total Porta a Porta: R$ {d['custo_casal_total']:.2f}")
        print(f"    Desconto: {d['desconto_pct']}% | Economia Casal: R$ {d['economia_casal']:.2f}")

    print("\n🟡 === TOP 3 ACHADOS EM JANELAS ALAVANCADAS COM TRE (1 a 2 FOLGAS) ===")
    for idx, d in enumerate(achados_tre[:3], 1):
        print(f"#{idx} | {d['destino']} via {d['origem']} | {d['data_ida']} a {d['data_volta']} ({d['nome_evento']})")
        print(f"    Tarifa: R$ {d['tarifa_pessoa']:.2f}/pessoa | Casal Total Porta a Porta: R$ {d['custo_casal_total']:.2f}")
        print(f"    Desconto: {d['desconto_pct']}% | Economia Casal: R$ {d['economia_casal']:.2f}")
        print(f"    TRE: {d['alavancagem_tre']}")

    if disparar_telegram:
        disparador = DisparadorAlerta()
        print("\n📲 Disparando o campeão de cada categoria para o Telegram...")
        # 1 Campeão Puro
        if achados_puros:
            d = achados_puros[0]
            msg_puro = formatar_alerta_novo_padrao(
                origem=d["origem"],
                origem_nome=d["origem_nome"],
                destino=d["destino"],
                destino_nome=d["destino_nome"],
                datas_label=f"{d['data_ida']} a {d['data_volta']} — {d['nome_evento']}",
                tarifa_pessoa=d["tarifa_pessoa"],
                cia_aerea=d["cia"],
                horario_ida=d["horario_ida"],
                horario_volta=d["horario_volta"],
                onibus_detalhe=sugerir_horario_onibus(d["horario_ida"], d["origem"]),
                url_reserva=d["url"],
                modo="html",
                alavancagem_tre=None
            )
            disparador.enviar_telegram(msg_puro)
            time.sleep(1.5)

        # 1 Campeão TRE
        if achados_tre:
            d = achados_tre[0]
            msg_tre = formatar_alerta_novo_padrao(
                origem=d["origem"],
                origem_nome=d["origem_nome"],
                destino=d["destino"],
                destino_nome=d["destino_nome"],
                datas_label=f"{d['data_ida']} a {d['data_volta']} — {d['nome_evento']}",
                tarifa_pessoa=d["tarifa_pessoa"],
                cia_aerea=d["cia"],
                horario_ida=d["horario_ida"],
                horario_volta=d["horario_volta"],
                onibus_detalhe=sugerir_horario_onibus(d["horario_ida"], d["origem"]),
                url_reserva=d["url"],
                modo="html",
                alavancagem_tre=d["alavancagem_tre"]
            )
            disparador.enviar_telegram(msg_tre)


if __name__ == "__main__":
    rodar_varredura_concomitante(disparar_telegram=True)
