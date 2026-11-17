"""
custo_porta_a_porta.py — AeroFolga / Vespasiano Labs
Motor de Decisão Logística e Custo Real "Porta a Porta" saindo de Volta Redonda.
Elimina a ilusão de passagens baratas em São Paulo ao somar ônibus, Uber, pernoite e cansaço.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


def carregar_parametros_logisticos(caminho_arquivo: Optional[str] = None) -> Dict[str, Any]:
    """Carrega os custos calibrados de data/custos_logisticos.json."""
    if caminho_arquivo:
        path = Path(caminho_arquivo)
    else:
        path = Path(__file__).parent.parent.parent / "data" / "custos_logisticos.json"

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class EstimativaLogistica:
    def __init__(
        self,
        aeroporto: str,
        regiao_polo: str,  # 'rio_de_janeiro' ou 'sao_paulo'
        empresa_onibus: str,
        custo_onibus_casal: float,
        custo_uber_casal: float,
        custo_pernoite: float,
        custo_alimentacao: float,
        horas_estrada_total: float,
        pernoite_necessario: bool
    ):
        self.aeroporto = aeroporto
        self.regiao_polo = regiao_polo
        self.empresa_onibus = empresa_onibus
        self.custo_onibus_casal = custo_onibus_casal
        self.custo_uber_casal = custo_uber_casal
        self.custo_pernoite = custo_pernoite
        self.custo_alimentacao = custo_alimentacao
        self.horas_estrada_total = horas_estrada_total
        self.pernoite_necessario = pernoite_necessario

        self.custo_logistico_total = (
            self.custo_onibus_casal
            + self.custo_uber_casal
            + self.custo_pernoite
            + self.custo_alimentacao
        )

    def to_dict(self) -> dict:
        return {
            "aeroporto": self.aeroporto,
            "regiao": "Rio de Janeiro" if self.regiao_polo == "rio_de_janeiro" else "São Paulo",
            "empresa_onibus": self.empresa_onibus,
            "onibus_casal_ida_volta": self.custo_onibus_casal,
            "uber_casal_ida_volta": self.custo_uber_casal,
            "pernoite_hotel_airbnb": self.custo_pernoite,
            "alimentacao_transito": self.custo_alimentacao,
            "custo_logistico_total": self.custo_logistico_total,
            "tempo_estrada_total_horas": self.horas_estrada_total,
            "requer_pernoite": self.pernoite_necessario
        }


def calcular_logistica(aeroporto: str, dados_logisticos: Optional[Dict[str, Any]] = None) -> EstimativaLogistica:
    """
    Calcula a logística de deslocamento saindo de Volta Redonda para o aeroporto desejado.
    """
    if dados_logisticos is None:
        dados_logisticos = carregar_parametros_logisticos()

    rotas = dados_logisticos["rotas_logisticas"]

    if aeroporto in ("GIG", "SDU"):
        polo = "rio_de_janeiro"
        cfg_polo = rotas[polo]
        cfg_aero = cfg_polo["aeroportos"][aeroporto]

        # 4 passagens de ônibus (Hugo ida/volta + Esposa ida/volta)
        custo_onibus = cfg_polo["tarifa_onibus_trecho_brl"] * 4
        # 2 corridas de Uber (Novo Rio -> Aeroporto na ida, Aeroporto -> Novo Rio na volta)
        custo_uber = cfg_aero["uber_medio_trecho_brl"] * 2
        custo_pernoite = 0.0
        custo_alim = 0.0
        horas_estrada = cfg_polo["tempo_onibus_horas_trecho"] * 2
        pernoite = False

    elif aeroporto in ("GRU", "CGH", "VCP"):
        polo = "sao_paulo"
        cfg_polo = rotas[polo]
        cfg_aero = cfg_polo["aeroportos"][aeroporto]

        custo_onibus = cfg_polo["tarifa_onibus_trecho_brl"] * 4
        custo_uber = cfg_aero["uber_medio_trecho_brl"] * 2
        custo_pernoite = cfg_polo["custo_pernoite_padrao_brl"]
        custo_alim = cfg_polo["alimentacao_transito_brl"]
        horas_estrada = cfg_polo["tempo_onibus_horas_trecho"] * 2
        pernoite = True
    else:
        # Fallback genérico
        return EstimativaLogistica(aeroporto, "outro", "Desconhecida", 0, 0, 0, 0, 0, False)

    return EstimativaLogistica(
        aeroporto=aeroporto,
        regiao_polo=polo,
        empresa_onibus=cfg_polo["empresa_onibus"],
        custo_onibus_casal=custo_onibus,
        custo_uber_casal=custo_uber,
        custo_pernoite=custo_pernoite,
        custo_alimentacao=custo_alim,
        horas_estrada_total=horas_estrada,
        pernoite_necessario=pernoite
    )


class ParecerPortaAPorta:
    def __init__(
        self,
        aeroporto: str,
        preco_passagem_pessoa: float,
        logistica: EstimativaLogistica
    ):
        self.aeroporto = aeroporto
        self.preco_passagem_pessoa = preco_passagem_pessoa
        self.passagens_casal = preco_passagem_pessoa * 2
        self.logistica = logistica
        self.custo_final_real_casal = self.passagens_casal + logistica.custo_logistico_total


def comparar_aeroportos(
    preco_rio_pessoa: float,
    aero_rio: str,
    preco_sp_pessoa: float,
    aero_sp: str
) -> dict:
    """
    Compara duas opções e emite o veredito determinístico do Motor de Decisão.
    """
    log_rio = calcular_logistica(aero_rio)
    log_sp = calcular_logistica(aero_sp)

    parecer_rio = ParecerPortaAPorta(aero_rio, preco_rio_pessoa, log_rio)
    parecer_sp = ParecerPortaAPorta(aero_sp, preco_sp_pessoa, log_sp)

    diferenca_final = parecer_sp.custo_final_real_casal - parecer_rio.custo_final_real_casal
    economia_bruta_passagem_casal = (preco_rio_pessoa - preco_sp_pessoa) * 2

    # Veredito
    if diferenca_final > 0:
        # SP é mais caro no custo real total
        selo = "🔴 FALSA ECONOMIA EM SP"
        recomendacao = (
            f"Voe pelo {aero_rio}! Embora a passagem em {aero_sp} pareça R$ {preco_rio_pessoa - preco_sp_pessoa:.2f} "
            f"mais barata por pessoa, ir por São Paulo fica R$ {diferenca_final:.2f} MAIS CARO no bolso do casal "
            f"devido a ônibus da Cometa, Uber e diária de Airbnb/hotel, além de somar 12 horas cansativas na Dutra."
        )
        escolha = aero_rio
    elif diferenca_final < -200:
        # SP é significativamente mais barato mesmo pagando hotel e Cometa
        selo = "💎 OPORTUNIDADE REAL EM SP"
        recomendacao = (
            f"Voe por {aero_sp}! A passagem está tão barata que, mesmo pagando ônibus da Cometa, "
            f"Uber e pernoite de R$ 250 em Airbnb/hotel, o casal ainda economiza R$ {abs(diferenca_final):.2f} líquidos!"
        )
        escolha = aero_sp
    else:
        # Empate técnico (diferença pequena)
        selo = "🟡 EMPATE TÉCNICO (PREFIRA O RIO)"
        recomendacao = (
            f"Financeiramente equivalentes (diferença de R$ {abs(diferenca_final):.2f}). "
            f"Recomendamos o {aero_rio} pelo conforto (viagem rápida de 2h via Cidade do Aço sem pernoite)."
        )
        escolha = aero_rio

    return {
        "escolha_recomendada": escolha,
        "selo": selo,
        "recomendacao": recomendacao,
        "opcao_rio": {
            "aeroporto": aero_rio,
            "passagem_pessoa": preco_rio_pessoa,
            "passagens_casal": parecer_rio.passagens_casal,
            "logistica_casal": log_rio.custo_logistico_total,
            "detalhes_logistica": log_rio.to_dict(),
            "custo_final_real_casal": parecer_rio.custo_final_real_casal
        },
        "opcao_sp": {
            "aeroporto": aero_sp,
            "passagem_pessoa": preco_sp_pessoa,
            "passagens_casal": parecer_sp.passagens_casal,
            "logistica_casal": log_sp.custo_logistico_total,
            "detalhes_logistica": log_sp.to_dict(),
            "custo_final_real_casal": parecer_sp.custo_final_real_casal
        },
        "diferenca_liquida_casal": diferenca_final
    }
