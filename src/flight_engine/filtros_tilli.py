"""
filtros_tilli.py — AeroFolga / Vespasiano Labs
Implementação dos 4 Pilares de Engenharia de Voo da Mesa Estratégica
com Trava Rígida de Conexão Humana (Anti-Pinga-Pinga e Anti-Espera Abusiva).
"""

from typing import Dict, Any, List


class PropostaVoo:
    def __init__(
        self,
        origem: str,
        destino: str,
        data_ida: str,
        data_volta: str,
        companhia: str,
        preco_brl: float,
        preco_historico_brl: float,
        num_escalas: int = 0,
        duracao_conexao_horas: float = 0.0,
        duracao_total_viagem_horas: float = 2.0,
        troca_aeroporto: bool = False,
        mala_de_mao_inclusa: bool = True,
        chega_no_dia_seguinte: bool = False,
        url_reserva: str = "",
        horario_ida: str = "",
        horario_volta: str = ""
    ):
        self.origem = origem
        self.destino = destino
        self.data_ida = data_ida
        self.data_volta = data_volta
        self.companhia = companhia
        self.preco_brl = preco_brl
        self.preco_historico_brl = preco_historico_brl
        self.num_escalas = num_escalas
        self.duracao_conexao_horas = duracao_conexao_horas
        self.duracao_total_viagem_horas = duracao_total_viagem_horas
        self.troca_aeroporto = troca_aeroporto
        self.mala_de_mao_inclusa = mala_de_mao_inclusa
        self.chega_no_dia_seguinte = chega_no_dia_seguinte
        self.url_reserva = url_reserva
        self.horario_ida = horario_ida
        self.horario_volta = horario_volta

        # Cálculo da economia
        if preco_historico_brl > 0:
            self.desconto_percentual = round((1 - (preco_brl / preco_historico_brl)) * 100, 1)
            self.economia_liquida_brl = round(preco_historico_brl - preco_brl, 2)
        else:
            self.desconto_percentual = 0.0
            self.economia_liquida_brl = 0.0

    @property
    def tem_conexao(self) -> bool:
        return self.num_escalas > 0

    def to_dict(self) -> dict:
        return {
            "rota": f"{self.origem} ⇄ {self.destino}",
            "periodo": f"{self.data_ida} até {self.data_volta}",
            "companhia": self.companhia,
            "preco_brl": self.preco_brl,
            "preco_historico_brl": self.preco_historico_brl,
            "desconto_percentual": f"{self.desconto_percentual}%",
            "economia_liquida_brl": f"R$ {self.economia_liquida_brl:.2f}",
            "num_escalas": self.num_escalas,
            "duracao_conexao_horas": self.duracao_conexao_horas,
            "duracao_total_viagem_horas": self.duracao_total_viagem_horas,
            "chega_no_dia_seguinte": self.chega_no_dia_seguinte,
            "mala_mao_inclusa": self.mala_de_mao_inclusa,
            "horario_ida": self.horario_ida,
            "horario_volta": self.horario_volta,
            "url_reserva": self.url_reserva
        }


def auditar_voo_pelos_4_pilares(
    voo: PropostaVoo,
    max_escalas_permitidas: int = 1,
    max_horas_conexao: float = 4.0,
    max_duracao_total_horas: float = 7.5
) -> tuple[bool, str]:
    """
    TRAVA RÍGIDA DE CONEXÃO HUMANA:
    Elimina voos pinga-pinga, conexões exaustivas e odisseias de 24 horas.
    Não pressupõe sala VIP (critério de cansaço real de aeroporto).
    """
    # Trava 1: Anti-Pinga-Pinga (máximo 1 escala permitida)
    if voo.num_escalas > max_escalas_permitidas:
        return False, f"Reprovado: Muitas escalas ({voo.num_escalas} escalas > {max_escalas_permitidas} máx)"

    # Trava 2: Chegada no dia seguinte (proíbe viagens de 24 horas)
    if voo.chega_no_dia_seguinte:
        return False, "Reprovado: Odisseia! Chegada no dia seguinte (quase 24 horas de viagem)"

    # Trava 3: Duração total excessiva da viagem (máx 7.5h para voos nacionais)
    if voo.duracao_total_viagem_horas > max_duracao_total_horas:
        return False, f"Reprovado: Duração total exaustiva ({voo.duracao_total_viagem_horas:.1f}h > {max_duracao_total_horas}h)"

    # Trava 4: Limite rígido de tempo de conexão (1h a 4h)
    if voo.tem_conexao:
        if voo.duracao_conexao_horas > max_horas_conexao:
            return False, f"Reprovado: Escala exaustiva ({voo.duracao_conexao_horas:.1f}h de espera > {max_horas_conexao}h máx)"
        if voo.duracao_conexao_horas < 0.8:
            return False, f"Reprovado: Conexão perigosa ({voo.duracao_conexao_horas:.1f}h < 50 min - risco de perder o voo)"

    # Trava 5: Anti-armadilha de aeroporto
    if voo.troca_aeroporto:
        return False, "Reprovado: Exige troca física de aeroporto (ex: CGH -> GRU)"

    # Trava 6: Auditoria de bagagem
    if not voo.mala_de_mao_inclusa:
        return False, "Reprovado: Não inclui mala de mão de 10kg"

    # Trava 7: Gatilho de preço promocional atípico (mínimo 40% de desconto)
    if voo.desconto_percentual < 40.0:
        return False, f"Reprovado: Desconto insuficiente ({voo.desconto_percentual}% < 40% mínimo)"

    return True, "Aprovado: Voo Humano e Confortável"
