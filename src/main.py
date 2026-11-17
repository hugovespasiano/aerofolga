"""
main.py — AeroFolga / Vespasiano Labs
Ponto de entrada do sistema: cruza calendários, audita passagens em múltiplos buscadores (Google Flights + Skiplagged)
e dispara alertas reais sem qualquer simulação.
"""

import sys
import argparse
from pathlib import Path

# Garante importações relativas a partir de src/
sys.path.append(str(Path(__file__).parent))

from calendar_engine.regras_servidor import PerfilCasal
from calendar_engine.calculadora_janelas import encontrar_janelas_ano
from flight_engine.consolidator import buscar_menor_tarifa_multiprovedor
from flight_engine.radar_voos import carregar_destinos_homologados
from notifier.formatador_alerta import formatar_alerta_whatsapp
from notifier.disparador import DisparadorAlerta


def executar_aerofolga(ano: int = 2026, saldo_tre: int = 4, disparar: bool = False, limite_janelas: int = 2):
    print("=" * 65)
    print("✈️  AEROFOLGA — RADAR INTELIGENTE MULTI-BUSCADOR (AO VIVO)")
    print("    Google Flights + Skiplagged | Sul Fluminense ⇄ Brasil")
    print("=" * 65)

    # 1. Configurar Perfil do Casal
    perfil = PerfilCasal(saldo_folgas_tre_hugo=saldo_tre)
    print(f"\n[1/3] 📅 Cruzando vínculos de Hugo (Itatiaia + SEEDUC BM) e Esposa (VR)...")
    janelas = encontrar_janelas_ano(ano, perfil)
    print(f"      Encontradas {len(janelas)} janelas de viagem viáveis para {ano}.")

    # 2. Executar Radar de Passagens Ao Vivo
    print(f"\n[2/3] 🛫 Consultando tarifas REAIS no Google Flights e Skiplagged...")
    destinos = carregar_destinos_homologados()
    disparador = DisparadorAlerta()
    alertas_gerados = 0

    # Analisa as primeiras janelas com busca ao vivo real
    for janela in janelas[:limite_janelas]:
        print(f"\n🔍 Varrendo Janela: {janela.to_dict()['periodo']} ({janela.dias_totais} dias)")
        
        for d in destinos[:2]:  # Foca nos principais destinos homologados
            destino_codigo = d["destino_codigo"]
            preco_hist = float(d["preco_medio_historico_brl"])
            
            print(f"   -> Buscando Rio (GIG) ⇄ {destino_codigo}...", end="", flush=True)
            voo_real = buscar_menor_tarifa_multiprovedor(
                origem="GIG",
                destino=destino_codigo,
                data_ida=janela.inicio.isoformat(),
                data_volta=janela.fim.isoformat(),
                preco_historico=preco_hist
            )

            if voo_real:
                print(f" Encontrado: R$ {voo_real.preco_brl:.2f} via {voo_real.companhia}")
                alertas_gerados += 1
                mensagem = formatar_alerta_whatsapp(janela, voo_real)
                disparador.enviar_console(mensagem)

                if disparar:
                    disparador.enviar_telegram(mensagem)
            else:
                print(" Sem disponibilidade no período.")

    print(f"\n[3/3] ✅ Concluído! {alertas_gerados} alertas reais gerados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AeroFolga — Radar de Voos e Folgas de Servidores")
    parser.add_argument("--ano", type=int, default=2026, help="Ano a ser analisado (padrão: 2026)")
    parser.add_argument("--tre", type=int, default=4, help="Saldo de folgas do TRE do Hugo (padrão: 4)")
    parser.add_argument("--disparar", action="store_true", help="Dispara no Telegram/WhatsApp além do console")
    parser.add_argument("--limite", type=int, default=2, help="Limite de janelas a consultar ao vivo (padrão: 2)")

    args = parser.parse_args()
    executar_aerofolga(ano=args.ano, saldo_tre=args.tre, disparar=args.disparar, limite_janelas=args.limite)
