"""
calculadora_janelas.py — AeroFolga / Vespasiano Labs
Calcula e agrupa dias livres contíguos do casal (3 a 7 dias)
gerando janelas de viagem atípicas e janelas alavancadas com Coringa TRE.
"""

from datetime import date, timedelta
from typing import List, Dict
from calendar_engine.feriados_fixos import mapa_feriados_por_data
from calendar_engine.regras_servidor import PerfilCasal, StatusDia


class JanelaViagem:
    def __init__(
        self,
        inicio: date,
        fim: date,
        dias_totais: int,
        tipo: str,
        custo_tre: int,
        detalhes: List[str]
    ):
        self.inicio = inicio
        self.fim = fim
        self.dias_totais = dias_totais
        self.tipo = tipo
        self.custo_tre = custo_tre
        self.detalhes = detalhes

    def to_dict(self) -> dict:
        dias_semana_pt = {
            0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui", 4: "Sex", 5: "Sáb", 6: "Dom"
        }
        ini_str = f"{self.inicio.strftime('%d/%m')} ({dias_semana_pt[self.inicio.weekday()]})"
        fim_str = f"{self.fim.strftime('%d/%m')} ({dias_semana_pt[self.fim.weekday()]})"

        return {
            "periodo": f"{ini_str} até {fim_str}",
            "inicio_iso": self.inicio.isoformat(),
            "fim_iso": self.fim.isoformat(),
            "dias_totais": self.dias_totais,
            "tipo": self.tipo,
            "custo_tre_dias": self.custo_tre,
            "detalhes": self.detalhes
        }

    def __repr__(self):
        return f"<Janela {self.inicio} a {self.fim} ({self.dias_totais} dias, TRE: {self.custo_tre})>"


def encontrar_janelas_ano(
    ano: int,
    perfil: PerfilCasal,
    min_dias: int = 3,
    max_tre_por_janela: int = 2
) -> List[JanelaViagem]:
    """
    Varre o ano calendário avaliando cada dia para o casal e agrupa sequências livres.
    """
    feriados_map = mapa_feriados_por_data(ano)
    dia_atual = date(ano, 1, 1)
    ultimo_dia = date(ano, 12, 31)

    historico_dias: Dict[date, dict] = {}
    while dia_atual <= ultimo_dia:
        historico_dias[dia_atual] = perfil.status_dia_casal(dia_atual, feriados_map)
        dia_atual += timedelta(days=1)

    # Identificar blocos contíguos de folga
    janelas: List[JanelaViagem] = []
    bloco_atual: List[tuple[date, dict]] = []

    dia_cursor = date(ano, 1, 1)
    while dia_cursor <= ultimo_dia:
        st = historico_dias[dia_cursor]

        # Consideramos elegível se ambos já estão livres ou se é possível cobrir com TRE
        if st["status"] in (StatusDia.LIVRE, StatusDia.CORINGA_TRE_POSSIVEL):
            bloco_atual.append((dia_cursor, st))
        else:
            # Fim do bloco anterior: avaliar se forma uma janela válida
            if len(bloco_atual) >= min_dias:
                _processar_bloco(bloco_atual, janelas, max_tre_por_janela)
            bloco_atual = []

        dia_cursor += timedelta(days=1)

    if len(bloco_atual) >= min_dias:
        _processar_bloco(bloco_atual, janelas, max_tre_por_janela)

    # Filtra e remove sobreposições redundantes
    return janelas


def _processar_bloco(
    bloco: List[tuple[date, dict]],
    janelas: List[JanelaViagem],
    max_tre_por_janela: int
):
    tre_usados = sum(1 for _, st in bloco if st["requer_tre"])
    if tre_usados > max_tre_por_janela:
        return

    inicio = bloco[0][0]
    fim = bloco[-1][0]
    total_dias = len(bloco)

    dias_semana_pt = {
        0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta",
        4: "Sexta", 5: "Sábado", 6: "Domingo"
    }
    tipo = f"{dias_semana_pt[inicio.weekday()]} a {dias_semana_pt[fim.weekday()]}"
    if tre_usados > 0:
        tipo += f" (Alavancado com {tre_usados} folga(s) TRE)"
    else:
        tipo += " (100% Puro - Sem gastar TRE)"

    detalhes = [f"{d.strftime('%d/%m')}: {st['detalhes']}" for d, st in bloco]

    janela = JanelaViagem(
        inicio=inicio,
        fim=fim,
        dias_totais=total_dias,
        tipo=tipo,
        custo_tre=tre_usados,
        detalhes=detalhes
    )
    janelas.append(janela)
