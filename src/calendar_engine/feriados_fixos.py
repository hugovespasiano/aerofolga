"""
feriados_fixos.py — AeroFolga / Vespasiano Labs
Calculadora matemática perpétua de feriados Nacionais, Estaduais (RJ)
e Municipais (Barra Mansa, Itatiaia e Volta Redonda).
"""

from datetime import date, timedelta
from typing import Dict, List, Optional


def calcular_pascoa(ano: int) -> date:
    """
    Calcula a data do Domingo de Páscoa pelo Algoritmo Gregoriano Anônimo (Meeus/Jones/Butcher).
    Válido para qualquer ano no calendário Gregoriano.
    """
    a = ano % 19
    b = ano // 100
    c = ano % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


class Feriado:
    def __init__(self, data: date, nome: str, esfera: str, legislacao: str = ""):
        self.data = data
        self.nome = nome
        self.esfera = esfera  # 'nacional', 'estadual_rj', 'municipal_bm', 'municipal_itatiaia', 'municipal_vr'
        self.legislacao = legislacao

    def to_dict(self) -> dict:
        return {
            "data": self.data.isoformat(),
            "nome": self.nome,
            "esfera": self.esfera,
            "legislacao": self.legislacao,
            "dia_da_semana": self.data.strftime("%A")
        }

    def __repr__(self):
        return f"<Feriado {self.data} - {self.nome} ({self.esfera})>"


def obter_feriados_ano(ano: int) -> List[Feriado]:
    """Retorna a lista completa de feriados para o ano informado."""
    feriados: List[Feriado] = []

    # 1. Datas Móveis baseadas na Páscoa
    pascoa = calcular_pascoa(ano)
    carnaval_segunda = pascoa - timedelta(days=48)
    carnaval_terca = pascoa - timedelta(days=47)
    quarta_cinzas = pascoa - timedelta(days=46)
    sexta_santa = pascoa - timedelta(days=2)
    corpus_christi = pascoa + timedelta(days=60)

    # 2. Feriados Nacionais (Lei 10.607/2002, Lei 6.802/1980 e Lei 14.759/2023)
    feriados_nacionais_fixos = [
        (date(ano, 1, 1), "Confraternização Universal", "Lei Federal nº 10.607/2002"),
        (date(ano, 4, 21), "Tiradentes", "Lei Federal nº 10.607/2002"),
        (date(ano, 5, 1), "Dia Mundial do Trabalho", "Lei Federal nº 10.607/2002"),
        (date(ano, 9, 7), "Independência do Brasil", "Lei Federal nº 10.607/2002"),
        (date(ano, 10, 12), "Nossa Senhora Aparecida (Padroeira do Brasil)", "Lei Federal nº 6.802/1980"),
        (date(ano, 11, 2), "Finados", "Lei Federal nº 10.607/2002"),
        (date(ano, 11, 15), "Proclamação da República", "Lei Federal nº 10.607/2002"),
        (date(ano, 11, 20), "Dia Nacional de Zumbi e da Consciência Negra", "Lei Federal nº 14.759/2023"),
        (date(ano, 12, 25), "Natal", "Lei Federal nº 10.607/2002"),
    ]

    for d, nome, leg in feriados_nacionais_fixos:
        feriados.append(Feriado(d, nome, "nacional", leg))

    feriados.append(Feriado(sexta_santa, "Sexta-feira Santa (Paixão de Cristo)", "nacional", "Lei Federal nº 9.093/1995"))
    feriados.append(Feriado(corpus_christi, "Corpus Christi", "nacional_religioso", "Decreto Municipal/Federal"))

    # 3. Feriados Estaduais do Rio de Janeiro
    feriados.append(Feriado(carnaval_terca, "Terça-feira de Carnaval", "estadual_rj", "Lei Estadual RJ nº 5.243/2008"))
    feriados.append(Feriado(date(ano, 4, 23), "Dia de São Jorge", "estadual_rj", "Lei Estadual RJ nº 5.198/2008"))

    # 4. Feriados Municipais — Barra Mansa (Lotação SEEDUC do Hugo)
    feriados.append(Feriado(date(ano, 1, 20), "São Sebastião (Padroeiro de Barra Mansa)", "municipal_bm", "Deliberação nº 48/1949"))
    feriados.append(Feriado(date(ano, 10, 3), "Aniversário de Barra Mansa", "municipal_bm", "Deliberação nº 48/1949"))

    # 5. Feriados Municipais — Itatiaia (Rede Municipal do Hugo)
    feriados.append(Feriado(date(ano, 3, 19), "São José (Padroeiro de Itatiaia)", "municipal_itatiaia", "Lei Municipal nº 410/2005"))
    feriados.append(Feriado(date(ano, 6, 1), "Emancipação Político-Administrativa de Itatiaia", "municipal_itatiaia", "Lei Municipal nº 410/2005"))

    # 6. Feriados Municipais — Volta Redonda (Lotação da Esposa)
    feriados.append(Feriado(date(ano, 6, 13), "Santo Antônio (Padroeiro de Volta Redonda)", "municipal_vr", "Lei Municipal nº 5.484/2018"))
    feriados.append(Feriado(date(ano, 7, 17), "Emancipação de Volta Redonda", "municipal_vr", "Lei Estadual nº 2.185/1954"))

    # Ordenar cronologicamente
    feriados.sort(key=lambda x: x.data)
    return feriados


def mapa_feriados_por_data(ano: int) -> Dict[date, List[Feriado]]:
    """Gera um dicionário onde a chave é a data e o valor é a lista de feriados naquele dia."""
    mapa: Dict[date, List[Feriado]] = {}
    for f in obter_feriados_ano(ano):
        if f.data not in mapa:
            mapa[f.data] = []
        mapa[f.data].append(f)
    return mapa
