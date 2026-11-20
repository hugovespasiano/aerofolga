"""
gerador_pontes_tre.py — AeroFolga / Vespasiano Labs
Motor de Geração de Janelas Alavancadas com Folga do TRE do Hugo.
Gera janelas em dias de semana + fins de semana e extensões de feriados (1 a 2 dias antes/depois).
"""

from datetime import date, timedelta
from typing import List, Dict
from calendar_engine.feriados_fixos import mapa_feriados_por_data, obter_feriados_ano


class JanelaAlavancadaTRE:
    def __init__(
        self,
        inicio: date,
        fim: date,
        modalidade: str,
        folgas_tre: int,
        dias_tre: List[str],
        descricao: str,
        is_extensao_feriado: bool = False,
        nome_feriado: str = ""
    ):
        self.inicio = inicio
        self.fim = fim
        self.dias_totais = (fim - inicio).days + 1
        self.modalidade = modalidade
        self.folgas_tre = folgas_tre
        self.dias_tre = dias_tre
        self.descricao = descricao
        self.is_extensao_feriado = is_extensao_feriado
        self.nome_feriado = nome_feriado

    @property
    def inicio_iso(self) -> str:
        return self.inicio.isoformat()

    @property
    def fim_iso(self) -> str:
        return self.fim.isoformat()

    def label_amigavel(self) -> str:
        dias_semana_pt = {0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui", 4: "Sex", 5: "Sáb", 6: "Dom"}
        return (
            f"{self.inicio.strftime('%d/%m')} ({dias_semana_pt[self.inicio.weekday()]}) a "
            f"{self.fim.strftime('%d/%m')} ({dias_semana_pt[self.fim.weekday()]}) — "
            f"{self.modalidade} ({self.dias_totais} dias, {self.folgas_tre} folga(s) TRE)"
        )

    def to_dict(self) -> dict:
        return {
            "inicio": self.inicio_iso,
            "fim": self.fim_iso,
            "dias_totais": self.dias_totais,
            "modalidade": self.modalidade,
            "folgas_tre": self.folgas_tre,
            "dias_tre": self.dias_tre,
            "descricao": self.descricao,
            "is_extensao_feriado": self.is_extensao_feriado,
            "nome_feriado": self.nome_feriado,
            "label": self.label_amigavel()
        }

    def __repr__(self):
        return f"<JanelaTRE {self.inicio_iso} a {self.fim_iso} ({self.modalidade}) - {self.folgas_tre}d TRE>"


def gerar_janelas_tre_ano(ano: int = 2027) -> List[JanelaAlavancadaTRE]:
    """
    Gera todas as combinações estratégicas onde até 2 folgas do TRE transformam
    dias de semana comuns ou feriados em janelas altamente lucrativas de viagem.
    """
    janelas: List[JanelaAlavancadaTRE] = []
    vistas = set()

    def adicionar(j: JanelaAlavancadaTRE):
        chave = (j.inicio, j.fim)
        if chave not in vistas and j.inicio.year == ano:
            vistas.add(chave)
            janelas.append(j)

    dias_semana_pt = {0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"}

    # 1. Extensões de Feriados Oficiais (1 ou 2 dias antes ou depois)
    feriados = obter_feriados_ano(ano)
    for f in feriados:
        d = f.data
        w = d.weekday()  # 0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sab, 6=Dom

        # Feriado na Quarta (ex: Tiradentes 21/04)
        if w == 2:
            # Opção A: Quarta a Domingo (5 dias) -> usa 2 folgas TRE: Quinta e Sexta
            adicionar(JanelaAlavancadaTRE(
                inicio=d,
                fim=d + timedelta(days=4),
                modalidade=f"{f.nome} Estendido (Qua ➔ Dom)",
                folgas_tre=2,
                dias_tre=[f"Quinta ({(d+timedelta(days=1)).strftime('%d/%m')})", f"Sexta ({(d+timedelta(days=2)).strftime('%d/%m')})"],
                descricao=f"Feriado na Quarta + 2 folgas TRE enforcando quinta e sexta até domingo",
                is_extensao_feriado=True,
                nome_feriado=f.nome
            ))
            # Opção B: Sábado anterior a Quarta (5 dias) -> usa 2 folgas TRE: Segunda e Terça
            adicionar(JanelaAlavancadaTRE(
                inicio=d - timedelta(days=4),
                fim=d,
                modalidade=f"{f.nome} Antecipado (Sáb ➔ Qua)",
                folgas_tre=2,
                dias_tre=[f"Segunda ({(d-timedelta(days=2)).strftime('%d/%m')})", f"Terça ({(d-timedelta(days=1)).strftime('%d/%m')})"],
                descricao=f"Sábado até feriado na Quarta usando 2 folgas TRE na segunda e terça",
                is_extensao_feriado=True,
                nome_feriado=f.nome
            ))

        # Feriado na Quinta (ex: Corpus Christi 27/05)
        elif w == 3:
            # Estendido até Terça-feira (6 dias): Quinta (feriado) + Sexta (ponto fac/TRE) + Sab + Dom + Seg + Ter
            adicionar(JanelaAlavancadaTRE(
                inicio=d,
                fim=d + timedelta(days=5),
                modalidade=f"{f.nome} Super Ponte (Qui ➔ Ter)",
                folgas_tre=2,
                dias_tre=[f"Sexta ({(d+timedelta(days=1)).strftime('%d/%m')})", f"Segunda ({(d+timedelta(days=4)).strftime('%d/%m')})"],
                descricao=f"Super janela de 6 dias pegando a volta na terça-feira com voos baratos",
                is_extensao_feriado=True,
                nome_feriado=f.nome
            ))
            # Padrão Quinta a Domingo (4 dias) com 1 folga TRE na sexta se não decretado ponto facultativo
            adicionar(JanelaAlavancadaTRE(
                inicio=d,
                fim=d + timedelta(days=3),
                modalidade=f"{f.nome} (Qui ➔ Dom)",
                folgas_tre=1,
                dias_tre=[f"Sexta ({(d+timedelta(days=1)).strftime('%d/%m')})"],
                descricao=f"Quinta a Domingo tradicional (usa 1 folga TRE se não houver ponto facultativo)",
                is_extensao_feriado=True,
                nome_feriado=f.nome
            ))

        # Feriado na Terça (ex: 07 de Setembro, 12 de Outubro)
        elif w == 1:
            # Antecipado: Quinta anterior até a Terça do feriado (6 dias) -> usa 2 folgas TRE: Quinta e Sexta
            adicionar(JanelaAlavancadaTRE(
                inicio=d - timedelta(days=5),
                fim=d,
                modalidade=f"{f.nome} Super Ponte (Qui ➔ Ter)",
                folgas_tre=2,
                dias_tre=[f"Quinta ({(d-timedelta(days=5)).strftime('%d/%m')})", f"Sexta ({(d-timedelta(days=4)).strftime('%d/%m')})"],
                descricao=f"Super janela de 6 dias viajando na quinta anterior e voltando no feriado",
                is_extensao_feriado=True,
                nome_feriado=f.nome
            ))
            # Sexta anterior até a Terça do feriado (5 dias) -> usa 1 folga TRE na segunda (se não decretado ponto)
            adicionar(JanelaAlavancadaTRE(
                inicio=d - timedelta(days=4),
                fim=d,
                modalidade=f"{f.nome} (Sex ➔ Ter)",
                folgas_tre=1,
                dias_tre=[f"Segunda ({(d-timedelta(days=1)).strftime('%d/%m')})"],
                descricao=f"Sexta a Terça emendando com o feriado",
                is_extensao_feriado=True,
                nome_feriado=f.nome
            ))

        # Feriado na Sexta (ex: Sexta Santa 26/03, São José 19/03 em Itatiaia)
        elif w == 4:
            # Estendido até Terça-feira (5 dias) -> usa 2 folgas TRE: Segunda e Terça
            adicionar(JanelaAlavancadaTRE(
                inicio=d,
                fim=d + timedelta(days=4),
                modalidade=f"{f.nome} Estendido (Sex ➔ Ter)",
                folgas_tre=2,
                dias_tre=[f"Segunda ({(d+timedelta(days=3)).strftime('%d/%m')})", f"Terça ({(d+timedelta(days=4)).strftime('%d/%m')})"],
                descricao=f"Feriado na Sexta + fim de semana + volta na Terça com 2 folgas TRE (evita voo caro de domingo)",
                is_extensao_feriado=True,
                nome_feriado=f.nome
            ))

        # Feriado na Segunda (ex: 15 de Novembro)
        elif w == 0:
            # Opção A: Quinta anterior até Segunda (5 dias) -> usa 2 folgas TRE: Quinta e Sexta
            adicionar(JanelaAlavancadaTRE(
                inicio=d - timedelta(days=4),
                fim=d,
                modalidade=f"{f.nome} Antecipado (Qui ➔ Seg)",
                folgas_tre=2,
                dias_tre=[f"Quinta ({(d-timedelta(days=4)).strftime('%d/%m')})", f"Sexta ({(d-timedelta(days=3)).strftime('%d/%m')})"],
                descricao=f"Quinta a Segunda emendando com feriado na segunda",
                is_extensao_feriado=True,
                nome_feriado=f.nome
            ))
            # Opção B: Sábado até Terça seguinte (4 dias) -> usa 1 folga TRE na terça
            adicionar(JanelaAlavancadaTRE(
                inicio=d - timedelta(days=2),
                fim=d + timedelta(days=1),
                modalidade=f"{f.nome} Estendido (Sáb ➔ Ter)",
                folgas_tre=1,
                dias_tre=[f"Terça ({(d+timedelta(days=1)).strftime('%d/%m')})"],
                descricao=f"Volta na terça pós-feriado com 1 folga TRE economizando na passagem",
                is_extensao_feriado=True,
                nome_feriado=f.nome
            ))

    # 2. Janelas Atípicas de Fim de Semana Comum (Sem feriado) em meses estratégicos
    # Varre cada semana do ano
    cursor = date(ano, 1, 1)
    # Alinha cursor para a primeira quinta-feira
    while cursor.weekday() != 3:
        cursor += timedelta(days=1)

    while cursor.year == ano:
        qui = cursor
        sex = qui + timedelta(days=1)
        sab = qui + timedelta(days=2)
        dom = qui + timedelta(days=3)
        seg = qui + timedelta(days=4)
        ter = qui + timedelta(days=5)

        # Meses de interesse (março, abril, maio, junho, agosto, setembro, outubro, novembro)
        # Evita apenas pico de férias se já monitorado ou foca nas semanas ordinárias
        mes = qui.month
        # Seleciona semanas estratégicas espaçadas (ex: 2ª e 4ª semana de cada mês de baixa/média temporada)
        dia_m = qui.day
        if 8 <= dia_m <= 22:
            # Padrão A: Quinta a Domingo (4 dias) — usa 2 folgas TRE (qui e sex)
            adicionar(JanelaAlavancadaTRE(
                inicio=qui,
                fim=dom,
                modalidade="Quinta a Domingo",
                folgas_tre=2,
                dias_tre=[f"Quinta ({qui.strftime('%d/%m')})", f"Sexta ({sex.strftime('%d/%m')})"],
                descricao="Fim de semana alavancado de 4 dias aproveitando tarifas baixas de quinta-feira"
            ))

            # Padrão B: Sábado a Terça (4 dias) — usa 2 folgas TRE (seg e ter)
            adicionar(JanelaAlavancadaTRE(
                inicio=sab,
                fim=ter,
                modalidade="Sábado a Terça",
                folgas_tre=2,
                dias_tre=[f"Segunda ({seg.strftime('%d/%m')})", f"Terça ({ter.strftime('%d/%m')})"],
                descricao="Retorno na Terça-feira com 2 folgas TRE (dia com os menores preços da semana)"
            ))

            # Padrão C: Sexta a Terça (5 dias) — usa 2 folgas TRE (seg e ter, sexta viagem pós-expediente ou flex)
            adicionar(JanelaAlavancadaTRE(
                inicio=sex,
                fim=ter,
                modalidade="Sexta a Terça",
                folgas_tre=2,
                dias_tre=[f"Segunda ({seg.strftime('%d/%m')})", f"Terça ({ter.strftime('%d/%m')})"],
                descricao="Janela de 5 dias completa com retorno na terça-feira barata"
            ))

            # Padrão D: Domingo a Terça (3 dias) — minitrip de 3 dias hiper econômica
            adicionar(JanelaAlavancadaTRE(
                inicio=dom,
                fim=ter,
                modalidade="Domingo a Terça",
                folgas_tre=2,
                dias_tre=[f"Segunda ({seg.strftime('%d/%m')})", f"Terça ({ter.strftime('%d/%m')})"],
                descricao="Escapada expressa de 3 dias aproveitando o contrafluxo das companhias aéreas"
            ))

        cursor += timedelta(days=7)

    # Ordena cronologicamente
    janelas.sort(key=lambda j: j.inicio)
    return janelas


if __name__ == "__main__":
    lista = gerar_janelas_tre_ano(2027)
    print(f"Total de janelas alavancadas com TRE geradas para 2027: {len(lista)}")
    print("\nExemplos de janelas geradas:")
    for j in lista[:10]:
        print(f" • {j.label_amigavel()} | Folgas: {', '.join(j.dias_tre)}")
