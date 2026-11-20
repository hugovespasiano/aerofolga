"""
radar_vigilante_runner.py — AeroFolga / Vespasiano Labs
Script autônomo para rodar em nuvem (GitHub Actions / Cron) com PC desligado.
Executa a varredura real, audita se o preço baixou mais ainda e dispara no Telegram.
"""

import os
import sys
import json
import time
import concurrent.futures
from pathlib import Path

# Ajusta caminho de importação
sys.path.append(str(Path(__file__).parent))

from fast_flights import FlightQuery, Passengers, create_query, get_flights
from calendar_engine.gerador_pontes_tre import gerar_janelas_tre_ano, JanelaAlavancadaTRE
from flight_engine.vigilante import VigilantePrecos
from notifier.disparador import DisparadorAlerta
from notifier.formatador_alerta import formatar_alerta_novo_padrao, sugerir_horario_onibus

# Janelas prioritárias do casal (Férias e Réveillon)
JANELAS_PRIORITARIAS = [
    ("2026-12-23", "2026-12-27", "Natal (23/12 a 27/12)", True, None),
    ("2026-12-30", "2027-01-03", "Réveillon (30/12 a 03/01)", True, None),
    ("2026-12-31", "2027-01-04", "Réveillon (31/12 a 04/01)", True, None),
    ("2027-01-04", "2027-01-08", "Janeiro (04/01 a 08/01)", True, None),
    ("2027-01-06", "2027-01-10", "Janeiro (06/01 a 10/01)", True, None)
]

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


def consultar_par(orig, dest_info, d_ida, d_volta, label, is_alta, alavancagem_tre):
    dest = dest_info["cod"]
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

        url = f"https://www.google.com/travel/flights?q=Flights%20to%20{dest}%20from%20{orig}%20on%20{d_ida}%20through%20{d_volta}"

        orig_nome = {"GIG": "Rio de Janeiro (Galeão)", "GRU": "São Paulo (Guarulhos)", "CGH": "São Paulo (Congonhas)"}.get(orig, orig)
        return {
            "origem": orig,
            "origem_nome": orig_nome,
            "destino": dest,
            "destino_nome": dest_info["nome"],
            "data_ida": d_ida,
            "data_volta": d_volta,
            "label": label,
            "is_alta": is_alta,
            "alavancagem_tre": alavancagem_tre,
            "preco": melhor.price,
            "cia": cia,
            "horario_ida": h_ida,
            "horario_volta": "Conforme opções do pacote",
            "url": url
        }
    except Exception:
        return None


def executar_ronda():
    print("🛰️  AeroFolga — Ronda do Vigilante de Preços iniciada...")
    vigilante = VigilantePrecos()
    disparador = DisparadorAlerta()

    # Monta lista de janelas a vigiar: Feriados prioritários + Janelas Alavancadas TRE
    janelas_vigilancia = list(JANELAS_PRIORITARIAS)

    # Adiciona janelas estratégicas de alavancagem TRE (Quinta a Domingo, Sábado a Terça, Sexta a Terça)
    try:
        janelas_tre = gerar_janelas_tre_ano(2027)
        # Seleciona as mais imediatas e com alto potencial de desconto (Março, Abril, Maio)
        for j in janelas_tre:
            if j.inicio.month in (3, 4, 5) and (j.modalidade in ("Quinta a Domingo", "Sábado a Terça") or j.is_extensao_feriado):
                alav_str = f"Usa {j.folgas_tre} folga(s) TRE ({', '.join(j.dias_tre)}) — {j.descricao}"
                janelas_vigilancia.append((j.inicio_iso, j.fim_iso, j.modalidade, False, alav_str))
    except Exception as e:
        print(f"Aviso: Não foi possível carregar janelas TRE: {e}")

    tarefas = []
    for d_ida, d_volta, label, is_alta, alav in janelas_vigilancia:
        for dest in DESTINOS:
            # Varre Galeão (GIG), Guarulhos (GRU) e Congonhas (CGH)
            tarefas.append(("GIG", dest, d_ida, d_volta, label, is_alta, alav))
            tarefas.append(("CGH", dest, d_ida, d_volta, label, is_alta, alav))

    print(f"Executando {len(tarefas)} verificações no radar...")
    encontrados = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futs = [executor.submit(consultar_par, *t) for t in tarefas]
        for f in concurrent.futures.as_completed(futs):
            res = f.result()
            if res:
                encontrados.append(res)

    print(f"Varredura concluída: {len(encontrados)} rotas com preço capturado.")

    alertas_enviados = 0
    for voo in encontrados:
        deve_alertar, motivo, preco_anterior = vigilante.auditar_queda_preco(
            voo["origem"], voo["destino"], voo["data_ida"], voo["data_volta"], voo["preco"]
        )

        # Tetos de alerta dinâmicos
        tetos = {"VIX": 550, "CWB": 860, "CNF": 925, "BSB": 950, "FLN": 1200, "NVT": 1000, "IGU": 1100, "SSA": 1500}
        teto = tetos.get(voo["destino"], 800)

        if deve_alertar and voo["preco"] <= teto:
            contexto = vigilante.avaliar_contexto_historico(voo["destino"], voo["preco"], is_alta_temporada=voo["is_alta"])

            # Prefixo se for queda de preço
            banner_queda = ""
            if "QUEDA" in motivo and preco_anterior:
                queda = preco_anterior - voo["preco"]
                banner_queda = f"📉 <b>O PREÇO CAIU MAIS! (-R$ {queda:.0f} por pessoa)</b>\n"

            msg = f"{banner_queda}" + formatar_alerta_novo_padrao(
                origem=voo["origem"],
                origem_nome=voo["origem_nome"],
                destino=voo["destino"],
                destino_nome=voo["destino_nome"],
                datas_label=f"{voo['data_ida']} a {voo['data_volta']} ({voo['label']})",
                tarifa_pessoa=float(voo["preco"]),
                cia_aerea=voo["cia"],
                horario_ida=voo["horario_ida"],
                horario_volta=voo["horario_volta"],
                onibus_detalhe=sugerir_horario_onibus(voo["horario_ida"], voo["origem"]),
                url_reserva=voo["url"],
                modo="html",
                alavancagem_tre=voo["alavancagem_tre"]
            )

            # Anexa termômetro histórico compacto
            msg += f"\n\n📊 <b>TERMÔMETRO HISTÓRICO:</b>\n" \
                   f"   • {contexto['veredicto']} (Típico nesta época: R$ {contexto['preco_tipico']})\n" \
                   f"   • <i>Menor do ano em baixa estação: R$ {contexto['piso_baixa']} ({contexto['meses_baratos']})</i>"

            print(f"🚨 Disparando alerta Telegram para {voo['destino']} (R$ {voo['preco']})...")
            disparador.enviar_telegram(msg)
            alertas_enviados += 1
            time.sleep(1)

    print(f"Ronda finalizada. Total de alertas disparados: {alertas_enviados}")


if __name__ == "__main__":
    executar_ronda()
