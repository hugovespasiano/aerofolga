import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from calendar_engine.regras_servidor import PerfilCasal
from calendar_engine.calculadora_janelas import encontrar_janelas_ano

def main():
    print("==================================================")
    print("🚀 AEROFOLGA — TESTE DE JANELAS REAIS DO CASAL")
    print("==================================================")
    perfil = PerfilCasal(saldo_folgas_tre_hugo=4)
    
    for ano in [2026, 2027]:
        janelas = encontrar_janelas_ano(ano, perfil)
        print(f"\n📅 ANO {ano}: {len(janelas)} JANELAS ENCONTRADAS")
        print("-" * 50)
        for i, j in enumerate(janelas, 1):
            d = j.to_dict()
            print(f"[{i}] {d['periodo']} ({d['dias_totais']} dias)")
            print(f"    Modalidade: {d['tipo']}")
            print(f"    Custo TRE: {d['custo_tre_dias']} dia(s)")
            for det in d['detalhes']:
                print(f"      • {det}")
            print()

if __name__ == "__main__":
    main()
