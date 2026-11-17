"""
main.py — AeroFolga / Vespasiano Labs
Ponto de entrada do sistema: cruza calendários, audita passagens e dispara alertas.
"""

import sys
import argparse
from pathlib import Path

# Garante importações relativas a partir de src/
sys.path.append(str(Path(__file__).parent))

from calendar_engine.regras_servidor import PerfilCasal
from calendar_engine.calculadora_janelas import encontrar_janelas_ano
from flight_engine.radar_voos import simular_radar_na_janela, carregar_destinos_homologados
from notifier.formatador_alerta import formatar_alerta_whatsapp
from notifier.disparador import DisparadorAlerta


def executar_aerofolga(ano: int = 2026, saldo_tre: int = 4, disparar: bool = False):
    print("=" * 60)
    print("✈️  AEROFOLGA — RADAR INTELIGENTE DE VIAGENS EM CASAL")
    print("    Vespasiano Labs | Sul Fluminense ⇄ Brasil/Mundo")
    print("=" * 60)

    # 1. Configurar Perfil do Casal
    perfil = PerfilCasal(saldo_folgas_tre_hugo=saldo_tre)
    print(f"\n[1/3] 📅 Cruzando vínculos de Hugo (Itatiaia + SEEDUC BM) e Esposa (VR)...")
    janelas = encontrar_janelas_ano(ano, perfil)
    print(f"      Encontradas {len(janelas)} janelas de viagem viáveis para {ano}.")

    # 2. Executar Radar de Passagens nos 4 Pilares
    print(f"\n[2/3] 🛫 Acionando radar de voos com os 4 Pilares da Mesa Estratégica...")
    destinos = carregar_destinos_homologados()
    print(f"      Destinos monitorados: {len(destinos)} rotas cadastradas.")

    disparador = DisparadorAlerta()
    alertas_gerados = 0

    for janela in janelas:
        voos = simular_radar_na_janela(
            inicio_iso=janela.inicio.isoformat(),
            fim_iso=janela.fim.isoformat(),
            destinos=destinos
        )

        for voo in voos:
            alertas_gerados += 1
            mensagem = formatar_alerta_whatsapp(janela, voo)
            disparador.enviar_console(mensagem)

            if disparar:
                # Tenta disparar no Telegram se configurado
                disparador.enviar_telegram(mensagem)
                # Tenta disparar no WhatsApp se configurado
                disparador.enviar_whatsapp(mensagem)

            # Limitamos a exibir as 2 melhores propostas por janela para não sobrecarregar
            break

    print(f"\n[3/3] ✅ Concluído! {alertas_gerados} alertas de alta relevância gerados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AeroFolga — Radar de Voos e Folgas de Servidores")
    parser.add_argument("--ano", type=int, default=2026, help="Ano a ser analisado (padrão: 2026)")
    parser.add_argument("--tre", type=int, default=4, help="Saldo de folgas do TRE do Hugo (padrão: 4)")
    parser.add_argument("--disparar", action="store_true", help="Dispara no Telegram/WhatsApp além do console")

    args = parser.parse_args()
    executar_aerofolga(ano=args.ano, saldo_tre=args.tre, disparar=args.disparar)
