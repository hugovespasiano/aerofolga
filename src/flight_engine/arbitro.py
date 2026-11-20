"""
arbitro.py — AeroFolga / Vespasiano Labs
Agente Árbitro de Consolidação, Deduplicação e Arbitragem Multi-Motor:
1. Recebe propostas de múltiplos motores (Google Flights, Kiwi, Skiplagged, Amadeus).
2. Deduplica voos idênticos (mesma rota, horário e cia) descartando versões mais caras/com taxas.
3. Arbitra e seleciona a menor tarifa absoluta real.
4. Identifica a natureza da tarifa (Voo Direto Puro, Combo Multicompanhia Kiwi, ou Cidade Oculta Skiplagged).
5. Garante que o usuário receba apenas 1 alerta definitivo no Telegram, sem repetições.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class OfertaNormalizada:
    def __init__(
        self,
        motor: str,
        origem: str,
        destino: str,
        data_ida: str,
        data_volta: str,
        preco_brl: float,
        cia_aerea: str,
        horario_ida: str,
        horario_volta: str,
        num_escalas: int,
        duracao_conexao_horas: float,
        duracao_total_horas: float,
        url_reserva: str,
        tipo_tarifa: str = "REGULAR", # REGULAR, COMBO_MULTICIA, SKIPLAGGED
        bagagem_mao_inclusa: bool = True
    ):
        self.motor = motor
        self.origem = origem
        self.destino = destino
        self.data_ida = data_ida
        self.data_volta = data_volta
        self.preco_brl = preco_brl
        self.cia_aerea = cia_aerea
        self.horario_ida = horario_ida
        self.horario_volta = horario_volta
        self.num_escalas = num_escalas
        self.duracao_conexao_horas = duracao_conexao_horas
        self.duracao_total_horas = duracao_total_horas
        self.url_reserva = url_reserva
        self.tipo_tarifa = tipo_tarifa
        self.bagagem_mao_inclusa = bagagem_mao_inclusa

    @property
    def assinatura_voo(self) -> str:
        """Chave para desduplicação de voos idênticos entre motores diferentes."""
        # Ex: GIG_CWB_2026-12-30_15:50_Gol
        return f"{self.origem}_{self.destino}_{self.data_ida}_{self.horario_ida[:5]}_{self.cia_aerea.split()[0]}"


class AgenteArbitroVoos:
    def __init__(self):
        pass

    def arbitrar_e_desduplicar(self, ofertas: List[OfertaNormalizada]) -> Optional[OfertaNormalizada]:
        """
        Deduplica ofertas idênticas e elege a campeã absoluta de melhor preço e conforto.
        """
        if not ofertas:
            return None

        # 1. Filtro dos 4 Pilares do Tilli (Conexão Humana)
        ofertas_validas = []
        for of in ofertas:
            # Rejeita voos com mais de 1 conexão
            if of.num_escalas > 1:
                continue
            # Rejeita escalas absurdas (> 4h)
            if of.duracao_conexao_horas > 4.0:
                continue
            # Rejeita viagens que ultrapassem 8 horas totais
            if of.duracao_total_horas > 8.0:
                continue
            ofertas_validas.append(of)

        if not ofertas_validas:
            return None

        # 2. Deduplicação inteligente de voos idênticos encontrados por mais de um buscador
        # Se Google Voos e outro buscador acharem o mesmo voo das 15:50 da Gol, mantemos o mais barato/sem taxas.
        mapa_desduplicado: Dict[str, OfertaNormalizada] = {}
        for of in ofertas_validas:
            chave = of.assinatura_voo
            if chave not in mapa_desduplicado:
                mapa_desduplicado[chave] = of
            else:
                # Se já existe, mantém o que tem o menor preço
                if of.preco_brl < mapa_desduplicado[chave].preco_brl:
                    mapa_desduplicado[chave] = of

        candidatas_finais = list(mapa_desduplicado.values())

        # 3. Eleição do campeão pelo menor preço em BRL
        campeao = min(candidatas_finais, key=lambda x: x.preco_brl)
        return campeao
