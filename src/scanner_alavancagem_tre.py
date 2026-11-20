"""
scanner_alavancagem_tre.py — AeroFolga / Vespasiano Labs
Varre janelas alavancadas com Banco de Folgas do TRE do Hugo (Quinta a Domingo, Sábado a Terça,
Sexta a Terça, Domingo a Terça e extensões de feriados em 1 ou 2 dias) ao longo de 2027.
Compara GIG, CGH e GRU, calcula custo porta a porta, % de desconto e dispara os maiores achados no Telegram.
"""

import sys
import time
import json
import concurrent.futures
from pathlib import Path
from datetime import date

sys.path.append(str(Path(__file__).parent))

from fast_flights import FlightQuery, Passengers, create_query, get_flights
from calendar_engine.gerador_pontes_tre import gerar_janelas_tre_ano, JanelaAlavancadaTRE
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


def consultar_voo(orig: str, dest_info: dict, janela: JanelaAlavancadaTRE):
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

        # Custo logística
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

        return {
            "origem": orig,
            "origem_nome": orig_nome,
            "destino": dest,
            "destino_nome": dest_info["nome"],
            "data_ida": d_ida,
            "data_volta": d_volta,
            "label": janela.label_amigavel(),
            "modalidade": janela.modalidade,
            "folgas_tre": janela.folgas_tre,
            "dias_tre": janela.dias_tre,
            "descricao_tre": janela.descricao,
            "tarifa_pessoa": melhor.price,
            "custo_casal_total": custo_casal_total,
            "cia": cia,
            "horario_ida": h_ida,
            "horario_volta": "Opções econômicas disponíveis",
            "url": url
        }
    except Exception:
        return None


def executar_varredura_tre(max_janelas: int = 15, disparar_telegram: bool = True):
    print("🚀 Iniciando Varredura de Janelas Alavancadas com Folga TRE (2027)...")
    todas_janelas = gerar_janelas_tre_ano(2027)

    # Filtra janelas mais atrativas em diferentes épocas do ano
    # (Março, Abril, Maio, Junho, Agosto, Setembro, Outubro, Novembro)
    janelas_selecionadas = []
    meses_alvo = [3, 4, 5, 6, 8, 9, 10, 11]

    for j in todas_janelas:
        if j.inicio.month in meses_alvo:
            # Seleciona uma mistura de Quinta a Domingo, Sábado a Terça e Extensões de Feriados
            janelas_selecionadas.append(j)

    # Pega uma amostra representativa de 16 janelas estratégicas ao longo do ano
    passo = max(1, len(janelas_selecionadas) // max_janelas)
    amostra_janelas = janelas_selecionadas[::passo][:max_janelas]

    print(f"Janelas selecionadas para teste ao vivo: {len(amostra_janelas)}")

    tarefas = []
    for j in amostra_janelas:
        for dest in DESTINOS:
            # Testa GIG e CGH
            tarefas.append(("GIG", dest, j))
            tarefas.append(("CGH", dest, j))

    print(f"Total de consultas planejadas: {len(tarefas)}...")
    encontrados = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futs = [executor.submit(consultar_voo, *t) for t in tarefas]
        for f in concurrent.futures.as_completed(futs):
            res = f.result()
            if res:
                encontrados.append(res)

    print(f"Consultas finalizadas! {len(encontrados)} voos reais encontrados.")

    # Ordena pelos melhores negócios: menor custo total casal
    encontrados.sort(key=lambda x: x["custo_casal_total"])

    # Carrega tabela de referência para calcular economia
    ref_path = Path(__file__).parent.parent / "data" / "tabela_referencia.json"
    ref_map = {}
    if ref_path.exists():
        with open(ref_path, "r", encoding="utf-8") as rf:
            ref_map = json.load(rf)

    # Identifica os Top 5 negócios absolutos
    top_deals = []
    destinos_vistos = set()

    for item in encontrados:
        d_cod = item["destino"]
        ref = ref_map.get(d_cod, {})
        preco_medio = float(ref.get("preco_medio_tipico", 1000.0))
        pct_desc = int(round(((preco_medio - item["tarifa_pessoa"]) / preco_medio) * 100))
        item["desconto_pct"] = pct_desc
        item["economia_casal"] = (preco_medio - item["tarifa_pessoa"]) * 2

        # Prioriza diversidade de destinos no topo
        chave_dest = (d_cod, item["origem"])
        if len(top_deals) < 6:
            if chave_dest not in destinos_vistos or len(destinos_vistos) >= 4:
                top_deals.append(item)
                destinos_vistos.add(chave_dest)

    print("\n🏆 --- TOP ACHADOS ALAVANCADOS COM FOLGA DO TRE ---")
    for idx, d in enumerate(top_deals, 1):
        print(f"#{idx} | {d['destino']} via {d['origem']} | {d['data_ida']} a {d['data_volta']} ({d['modalidade']})")
        print(f"    Passagem: R$ {d['tarifa_pessoa']:.2f}/pessoa | Total Casal Porta a Porta: R$ {d['custo_casal_total']:.2f}")
        print(f"    Desconto: {d['desconto_pct']}% | Economia Casal: R$ {d['economia_casal']:.2f}")
        print(f"    TRE: {d['folgas_tre']} folga(s) ({', '.join(d['dias_tre'])})")

    if disparar_telegram and top_deals:
        print("\n📲 Disparando os melhores alertas formatados para o Telegram...")
        disparador = DisparadorAlerta()
        for d in top_deals[:4]:  # Envia os 4 melhores para não inundar
            dias_tre_str = ", ".join(d["dias_tre"])
            alav_str = f"Usa {d['folgas_tre']} folga(s) TRE ({dias_tre_str}) — {d['descricao_tre']}"

            msg = formatar_alerta_novo_padrao(
                origem=d["origem"],
                origem_nome=d["origem_nome"],
                destino=d["destino"],
                destino_nome=d["destino_nome"],
                datas_label=f"{d['data_ida']} a {d['data_volta']} — {d['modalidade']}",
                tarifa_pessoa=d["tarifa_pessoa"],
                cia_aerea=d["cia"],
                horario_ida=d["horario_ida"],
                horario_volta=d["horario_volta"],
                onibus_detalhe=sugerir_horario_onibus(d["horario_ida"], d["origem"]),
                url_reserva=d["url"],
                modo="html",
                alavancagem_tre=alav_str
            )

            disparador.enviar_telegram(msg)
            time.sleep(1.5)
        print("Alertas enviados com sucesso para o Telegram!")

    return top_deals


if __name__ == "__main__":
    executar_varredura_tre(max_janelas=12, disparar_telegram=True)
