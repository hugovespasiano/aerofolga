"""
filtros_tilli.py — AeroFolga / Vespasiano Labs
Implementação dos 4 Pilares de Engenharia de Voo da Mesa Estratégica.
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
        tem_conexao: bool = False,
        duracao_conexao_horas: float = 0.0,
        troca_aeroporto: bool = False,
        mala_de_mao_inclusa: bool = True,
        url_reserva: str = ""
    ):
        self.origem = origem
        self.destino = destino
        self.data_ida = data_ida
        self.data_volta = data_volta
        self.companhia = companhia
        self.preco_brl = preco_brl
        self.preco_historico_brl = preco_historico_brl
        self.tem_conexao = tem_conexao
        self.duracao_conexao_horas = duracao_conexao_horas
        self.troca_aeroporto = troca_aeroporto
        self.mala_de_mao_inclusa = mala_de_mao_inclusa
        self.url_reserva = url_reserva

        # Cálculo da economia
        if preco_historico_brl > 0:
            self.desconto_percentual = round((1 - (preco_brl / preco_historico_brl)) * 100, 1)
            self.economia_liquida_brl = round(preco_historico_brl - preco_brl, 2)
        else:
            self.desconto_percentual = 0.0
            self.economia_liquida_brl = 0.0

    def to_dict(self) -> dict:
        return {
            "rota": f"{self.origem} ⇄ {self.destino}",
            "periodo": f"{self.data_ida} até {self.data_volta}",
            "companhia": self.companhia,
            "preco_brl": self.preco_brl,
            "preco_historico_brl": self.preco_historico_brl,
            "desconto_percentual": f"{self.desconto_percentual}%",
            "economia_liquida_brl": f"R$ {self.economia_liquida_brl:.2f}",
            "mala_mao_inclusa": self.mala_de_mao_inclusa,
            "tem_conexao": self.tem_conexao,
            "duracao_conexao_horas": self.duracao_conexao_horas,
            "url_reserva": self.url_reserva
        }


def auditar_voo_pelos_4_pilares(voo: PropostaVoo, max_horas_conexao: float = 3.5) -> tuple[bool, str]:
    """
    Aplica a auditoria rigorosa dos 4 Pilares:
    - Reprova sumariamente se houver troca de aeroporto.
    - Reprova se conexão exceder o limite humano (máx 3h a 3.5h).
    - Reprova se mala de mão não estiver inclusa (taxa oculta).
    - Reprova se o desconto real for inferior a 40% da média histórica.
    """
    # Pilar 3: Anti-armadilha de aeroporto
    if voo.troca_aeroporto:
        return False, "Reprovado: Exige troca física de aeroporto (ex: CGH -> GRU)"

    # Pilar 3: Conexões humanas
    if voo.tem_conexao and voo.duracao_conexao_horas > max_horas_conexao:
        return False, f"Reprovado: Conexão abusiva ({voo.duracao_conexao_horas}h > {max_horas_conexao}h)"

    # Pilar 4: Auditoria de bagagem
    if not voo.mala_de_mao_inclusa:
        return False, "Reprovado: Não inclui mala de mão de 10kg"

    # Pilar 4: Gatilho de preço promocional atípico (mínimo 40% de desconto)
    if voo.desconto_percentual < 40.0:
        return False, f"Reprovado: Desconto insuficiente ({voo.desconto_percentual}% < 40% mínimo)"

    return True, "Aprovado com Louvor nos 4 Pilares"
