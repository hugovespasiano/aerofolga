"""
executar_varredura_arbitrada.py — AeroFolga / Vespasiano Labs
Executa a busca multi-motor com arbitragem e deduplicação inteligente para
20 de Dezembro de 2026 a 10 de Janeiro de 2027.
"""

import sys
import json
import time
import concurrent.futures
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from flight_engine.consolidator import consolidar_todos_os_motores
from notifier.disparador import DisparadorAlerta
from notifier.formatador_alerta import formatar_alerta_novo_padrao, sugerir_horario_onibus

janelas = [
    # Natal
    ("2026-12-21", "2026-12-25", "Semana do Natal (21 a 25/12)"),
    ("2026-12-23", "2026-12-27", "Natal (23 a 27/12)"),
    ("2026-12-24", "2026-12-28", "Natal (24 a 28/12)"),
    # Entre Natal e Réveillon
    ("2026-12-26", "2026-12-30", "Fim de Ano (26 a 30/12)"),
    ("2026-12-27", "2026-12-31", "Fim de Ano (27 a 31/12)"),
    # Réveillon (Virada)
    ("2026-12-29", "2027-01-02", "Réveillon (29/12 a 02/01)"),
    ("2026-12-30", "2027-01-03", "Réveillon (30/12 a 03/01)"),
    ("2026-12-31", "2027-01-04", "Réveillon (31/12 a 04/01)"),
    # Janeiro (Pós-Réveillon)
    ("2027-01-03", "2027-01-07", "Janeiro (03 a 07/01)"),
    ("2027-01-04", "2027-01-08", "Janeiro (04 a 08/01)"),
    ("2027-01-05", "2027-01-09", "Janeiro (05 a 09/01)"),
    ("2027-01-06", "2027-01-10", "Janeiro (06 a 10/01)")
]

destinos = [
    ("VIX", "Vitória (ES)"),
    ("CWB", "Curitiba (PR)"),
    ("CNF", "Belo Horizonte (MG)"),
    ("BSB", "Brasília (DF)"),
    ("FLN", "Florianópolis (SC)"),
    ("SSA", "Salvador (BA)")
]

def buscar_par(orig, dest_tuple, ida, volta, label):
    dest, dest_nome = dest_tuple
    try:
        oferta = consolidar_todos_os_motores(orig, dest, ida, volta)
        if oferta:
            return {
                "origem": orig,
                "origem_nome": "Rio de Janeiro",
                "destino": dest,
                "destino_nome": dest_nome,
                "ida": ida,
                "volta": volta,
                "label": label,
                "preco": oferta.preco_brl,
                "cia": oferta.cia_aerea,
                "motor": oferta.motor,
                "tipo_tarifa": oferta.tipo_tarifa,
                "horario_ida": oferta.horario_ida,
                "horario_volta": oferta.horario_volta,
                "url": oferta.url_reserva
            }
    except Exception:
        pass
    return None

def main():
    tarefas = []
    for ida, volta, label in janelas:
        for d in destinos:
            tarefas.append(("GIG", d, ida, volta, label))

    print(f"🚀 Iniciando Varredura Arbitrada Multi-Motor: {len(tarefas)} combinações (20/12 a 10/01)...")
    vencedores = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futs = [executor.submit(buscar_par, *t) for t in tarefas]
        for f in concurrent.futures.as_completed(futs):
            res = f.result()
            if res:
                vencedores.append(res)

    vencedores.sort(key=lambda x: x["preco"])

    print("\n🏆 TOP 10 MELHORES VIAGENS ARBITRADAS (20/12 a 10/01):")
    for v in vencedores[:10]:
        print(f"R$ {v['preco']:>4} | {v['origem']} ➔ {v['destino']} ({v['destino_nome']}) | {v['label']} | {v['cia']} | via {v['motor']}")

    # Salva no disco
    with open("data/resultados_arbitrados_fim_ano.json", "w", encoding="utf-8") as out:
        json.dump(vencedores, out, indent=2, ensure_ascii=False)

    # Dispara os 3 melhores campeões para o Telegram
    disp = DisparadorAlerta()
    print("\n📲 Disparando os 3 maiores achados arbitrados para o Telegram...")

    for v in vencedores[:3]:
        detalhe_onibus = sugerir_horario_onibus(v["horario_ida"], v["origem"])
        cia_rotulo = f"{v['cia']} [via {v['motor']}]"
        
        msg = formatar_alerta_novo_padrao(
            origem=v["origem"],
            origem_nome=v["origem_nome"],
            destino=v["destino"],
            destino_nome=v["destino_nome"],
            datas_label=f"{v['ida']} a {v['volta']} ({v['label']})",
            tarifa_pessoa=float(v["preco"]),
            cia_aerea=cia_rotulo,
            horario_ida=v["horario_ida"] or "Opções diretas",
            horario_volta=v["horario_volta"] or "Conforme pacote",
            onibus_detalhe=detalhe_onibus,
            url_reserva=v["url"],
            modo="html"
        )
        disp.enviar_telegram(msg)
        time.sleep(1)

    print("✅ Varredura arbitrada e disparos concluídos!")

if __name__ == "__main__":
    main()
