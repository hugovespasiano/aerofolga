import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from notifier.disparador import DisparadorAlerta
from notifier.formatador_alerta import formatar_alerta_novo_padrao

disp = DisparadorAlerta()

# 1. VITÓRIA (VIX) - Oportunidade Campeã
msg_vitoria = formatar_alerta_novo_padrao(
    origem="GIG",
    origem_nome="Rio de Janeiro",
    destino="VIX",
    destino_nome="Vitória (ES)",
    datas_label="06/01/2027 a 10/01/2027 (4 noites / 5 dias)",
    tarifa_pessoa=535.0,
    cia_aerea="Gol - Voo Direto",
    horario_ida="19:05 ➔ 20:15 (06/01)",
    horario_volta="07:55 ➔ 09:05 ou 10:25 ➔ 11:30 (10/01)",
    onibus_detalhe="Embarque às 14:00 (Cidade do Aço - Rodoviária Francisco Torres). Chegada na Novo Rio ~16:15 + 25 min Uber até GIG (~16:40), garantindo mais de 2h de folga contra retenções na Serra das Araras e Dutra.",
    url_reserva="https://www.google.com/travel/flights?q=Flights%20to%20VIX%20from%20GIG%20on%202027-01-06%20through%202027-01-10",
    modo="html"
)

# 2. CURITIBA (CWB) - Réveillon / Virada do Ano
msg_curitiba = formatar_alerta_novo_padrao(
    origem="GIG",
    origem_nome="Rio de Janeiro",
    destino="CWB",
    destino_nome="Curitiba (PR)",
    datas_label="30/12/2026 a 03/01/2027 (4 noites - Réveillon)",
    tarifa_pessoa=855.0,
    cia_aerea="Gol / LATAM - Voo Direto",
    horario_ida="15:50 ➔ 17:25 (30/12)",
    horario_volta="23:00 ➔ 00:30 (03/01)",
    onibus_detalhe="Embarque às 11:00 (Cidade do Aço). Chegada na Novo Rio ~13:15 + Uber até GIG (~13:45), garantindo 2h de antecedência no aeroporto com tranquilidade na Serra das Araras.",
    url_reserva="https://www.google.com/travel/flights?q=Flights%20to%20CWB%20from%20GIG%20on%202026-12-30%20through%202027-01-03",
    modo="html"
)

print("Enviando Oferta 1 (Vitória) para o Telegram...")
ok1 = disp.enviar_telegram(msg_vitoria)

print("Enviando Oferta 2 (Curitiba Réveillon) para o Telegram...")
ok2 = disp.enviar_telegram(msg_curitiba)

print(f"Status envios: VIX={ok1}, CWB={ok2}")
