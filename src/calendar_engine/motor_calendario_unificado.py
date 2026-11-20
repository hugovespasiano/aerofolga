"""
motor_calendario_unificado.py — AeroFolga / Vespasiano Labs
Motor Unificado de Calendário do Casal (SEEDUC, Itatiaia, Volta Redonda e TRE).
Combina CONCOMITANTEMENTE:
1. Janelas 100% PURAS (0 folgas TRE): Feriados oficiais, pontos facultativos clássicos, fins de semana prolongados e recessos.
2. Janelas ALAVANCADAS TRE (1 a 2 folgas TRE):
   - Extensões de feriados (1 a 2 dias antes ou depois para fugir das tarifas caras);
   - Fins de semana prolongados atípicos (Quinta a Domingo, Sábado a Terça, Sexta a Terça, Domingo a Terça).
"""

from datetime import date, timedelta
from typing import List, Dict, Optional
from calendar_engine.feriados_fixos import obter_feriados_ano, Feriado


class JanelaUnificada:
    CATEGORIA_PURO = "100% PURO (0 Folgas)"
    CATEGORIA_ALAVANCADO = "ALAVANCADO COM FOLGA"

    def __init__(
        self,
        inicio: date,
        fim: date,
        nome_evento: str,
        categoria: str,
        folgas_gastas: int,
        dias_folga: List[str],
        detalhes: str,
        is_alta_temporada: bool = False
    ):
        self.inicio = inicio
        self.fim = fim
        self.dias_totais = (fim - inicio).days + 1
        self.nome_evento = nome_evento
        self.categoria = categoria
        self.folgas_gastas = folgas_gastas
        self.dias_folga = dias_folga
        self.detalhes = detalhes
        self.is_alta_temporada = is_alta_temporada

    # Mantém compatibilidade com código existente
    @property
    def folgas_tre_gastas(self) -> int:
        return self.folgas_gastas

    @property
    def dias_tre(self) -> List[str]:
        return self.dias_folga

    @property
    def inicio_iso(self) -> str:
        return self.inicio.isoformat()

    @property
    def fim_iso(self) -> str:
        return self.fim.isoformat()

    def label_amigavel(self) -> str:
        dias_semana_pt = {0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui", 4: "Sex", 5: "Sáb", 6: "Dom"}
        ini_str = f"{self.inicio.strftime('%d/%m')} ({dias_semana_pt[self.inicio.weekday()]})"
        fim_str = f"{self.fim.strftime('%d/%m')} ({dias_semana_pt[self.fim.weekday()]})"
        tag = "🟢 100% PURO" if self.folgas_gastas == 0 else f"🟡 USA {self.folgas_gastas} FOLGA(S)"
        return f"{ini_str} a {fim_str} — {self.nome_evento} [{tag}, {self.dias_totais} dias]"

    def to_dict(self) -> dict:
        return {
            "inicio": self.inicio_iso,
            "fim": self.fim_iso,
            "dias_totais": self.dias_totais,
            "nome_evento": self.nome_evento,
            "categoria": self.categoria,
            "folgas_gastas": self.folgas_gastas,
            "dias_folga": self.dias_folga,
            "detalhes": self.detalhes,
            "is_alta_temporada": self.is_alta_temporada,
            "label": self.label_amigavel()
        }

    def __repr__(self):
        return f"<JanelaUnificada {self.inicio_iso} a {self.fim_iso} ({self.nome_evento}) - Folgas: {self.folgas_gastas}>"


def obter_janelas_unificadas_ano(ano: int = 2027) -> List[JanelaUnificada]:
    """
    Retorna o calendário completo unificado:
    - Todas as janelas puras (feriados + pontos facultativos decretados/tradicionais)
    - Concomitantemente, todas as janelas alavancadas com saldo do TRE do Hugo.
    """
    janelas: List[JanelaUnificada] = []
    chaves_vistas = set()

    def adicionar(j: JanelaUnificada):
        chave = (j.inicio, j.fim, j.folgas_tre_gastas)
        if chave not in chaves_vistas and j.inicio.year == ano:
            chaves_vistas.add(chave)
            janelas.append(j)

    dias_semana_pt = {0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui", 4: "Sex", 5: "Sáb", 6: "Dom"}

    # =========================================================================
    # PARTE 1: FERIADOS OFICIAIS, PONTOS FACULTATIVOS E EMENDAS PURAS (0 TRE)
    # =========================================================================
    feriados = obter_feriados_ano(ano)
    for f in feriados:
        d = f.data
        w = d.weekday()  # 0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sab, 6=Dom

        # Feriado na Sexta (Ex: 01/01 Confraternização, 19/03 São José Itatiaia, 26/03 Paixão de Cristo, 23/04 São Jorge RJ)
        if w == 4:
            # Puro: Sexta a Domingo (3 dias)
            adicionar(JanelaUnificada(
                inicio=d,
                fim=d + timedelta(days=2),
                nome_evento=f"{f.nome} (Feriadão Puro)",
                categoria=JanelaUnificada.CATEGORIA_PURO,
                folgas_tre_gastas=0,
                dias_tre=[],
                detalhes="Feriado oficial na sexta + fim de semana. Zero uso de folgas TRE.",
                is_alta_temporada=True
            ))
            # Concomitantemente com TRE: Estende até Terça (5 dias) com 2 folgas TRE
            adicionar(JanelaUnificada(
                inicio=d,
                fim=d + timedelta(days=4),
                nome_evento=f"{f.nome} Estendido até Terça",
                categoria=JanelaUnificada.CATEGORIA_ALAVANCADO_TRE,
                folgas_tre_gastas=2,
                dias_tre=[f"Segunda ({(d+timedelta(days=3)).strftime('%d/%m')})", f"Terça ({(d+timedelta(days=4)).strftime('%d/%m')})"],
                detalhes="Feriado na sexta + fim de semana + 2 folgas TRE na seg/ter (fuga do voo caro de domingo)",
                is_alta_temporada=True
            ))

        # Feriado na Quinta (Ex: 27/05 Corpus Christi)
        elif w == 3:
            # Puro com Ponto Facultativo decretado na Sexta: Quinta a Domingo (4 dias)
            adicionar(JanelaUnificada(
                inicio=d,
                fim=d + timedelta(days=3),
                nome_evento=f"{f.nome} (Ponte Pura com Ponto Facultativo)",
                categoria=JanelaUnificada.CATEGORIA_PURO,
                folgas_tre_gastas=0,
                dias_tre=[],
                detalhes="Feriado oficial na quinta + ponto facultativo tradicional do Estado/Municípios na sexta + fim de semana.",
                is_alta_temporada=True
            ))
            # Concomitantemente com TRE: Super Ponte até Terça (6 dias) com 1 ou 2 folgas TRE
            adicionar(JanelaUnificada(
                inicio=d,
                fim=d + timedelta(days=5),
                nome_evento=f"{f.nome} Super Ponte até Terça",
                categoria=JanelaUnificada.CATEGORIA_ALAVANCADO_TRE,
                folgas_tre_gastas=2,
                dias_tre=[f"Sexta ({(d+timedelta(days=1)).strftime('%d/%m')})", f"Segunda ({(d+timedelta(days=4)).strftime('%d/%m')})"],
                detalhes="6 dias contíguos de Quinta a Terça usando folga TRE na segunda e retorno na terça econômica.",
                is_alta_temporada=True
            ))

        # Feriado na Terça (Ex: 09/02 Carnaval, 01/06 Itatiaia, 07/09 Independência, 12/10 Aparecida, 02/11 Finados)
        elif w == 1:
            # Puro com Ponto Facultativo decretado na Segunda: Sábado a Terça (4 dias)
            adicionar(JanelaUnificada(
                inicio=d - timedelta(days=3),
                fim=d,
                nome_evento=f"{f.nome} (Ponte Pura Sáb ➔ Ter)",
                categoria=JanelaUnificada.CATEGORIA_PURO,
                folgas_tre_gastas=0,
                dias_tre=[],
                detalhes="Fim de semana + ponto facultativo de segunda + feriado oficial na terça. Zero folgas TRE.",
                is_alta_temporada=True
            ))
            # Concomitantemente com TRE: Antecipado para Quinta anterior (6 dias)
            adicionar(JanelaUnificada(
                inicio=d - timedelta(days=5),
                fim=d,
                nome_evento=f"{f.nome} Super Ponte Antecipada (Qui ➔ Ter)",
                categoria=JanelaUnificada.CATEGORIA_ALAVANCADO_TRE,
                folgas_tre_gastas=2,
                dias_tre=[f"Quinta ({(d-timedelta(days=5)).strftime('%d/%m')})", f"Sexta ({(d-timedelta(days=4)).strftime('%d/%m')})"],
                detalhes="6 dias contíguos saindo na quinta com 2 folgas TRE, voltando no feriado da terça.",
                is_alta_temporada=True
            ))

        # Feriado na Segunda (Ex: 15/11 Proclamação da República)
        elif w == 0:
            # Puro: Sábado a Segunda (3 dias) ou Sexta à noite a Segunda
            adicionar(JanelaUnificada(
                inicio=d - timedelta(days=2),
                fim=d,
                nome_evento=f"{f.nome} (Feriadão Puro Sáb ➔ Seg)",
                categoria=JanelaUnificada.CATEGORIA_PURO,
                folgas_tre_gastas=0,
                dias_tre=[],
                detalhes="Sábado a Segunda com feriado nacional. Zero folgas TRE.",
                is_alta_temporada=True
            ))
            # Concomitantemente com TRE: Estende até Terça (4 dias com 1 folga TRE na terça)
            adicionar(JanelaUnificada(
                inicio=d - timedelta(days=2),
                fim=d + timedelta(days=1),
                nome_evento=f"{f.nome} Estendido até Terça",
                categoria=JanelaUnificada.CATEGORIA_ALAVANCADO_TRE,
                folgas_tre_gastas=1,
                dias_tre=[f"Terça ({(d+timedelta(days=1)).strftime('%d/%m')})"],
                detalhes="Volta na terça-feira com 1 folga TRE para pegar passagens 40% a 50% mais baratas que a segunda.",
                is_alta_temporada=True
            ))

        # Feriado na Quarta (Ex: 21/04 Tiradentes - no RJ coincide com 23/04 São Jorge na sexta!)
        elif w == 2:
            if d.month == 4 and d.day == 21:
                # Caso Especial do RJ: Tiradentes 21/04 (Qua) e São Jorge 23/04 (Sex)!
                # Dia 22/04 (Quinta) é tradicionalíssimo Ponto Facultativo estadual no RJ:
                adicionar(JanelaUnificada(
                    inicio=d,
                    fim=d + timedelta(days=4),
                    nome_evento="Mega Feriado RJ Tiradentes + São Jorge (Qua ➔ Dom)",
                    categoria=JanelaUnificada.CATEGORIA_PURO,
                    folgas_tre_gastas=0,
                    dias_tre=[],
                    detalhes="5 dias puros: Quarta (Tiradentes), Quinta (Ponto Facultativo RJ), Sexta (São Jorge RJ), Sáb e Dom.",
                    is_alta_temporada=True
                ))
            else:
                # Quarta normal (ex: São Sebastião 20/01 em BM):
                # Com TRE: Quarta a Domingo (5 dias) com 2 folgas TRE
                adicionar(JanelaUnificada(
                    inicio=d,
                    fim=d + timedelta(days=4),
                    nome_evento=f"{f.nome} Estendido (Qua ➔ Dom)",
                    categoria=JanelaUnificada.CATEGORIA_ALAVANCADO_TRE,
                    folgas_tre_gastas=2,
                    dias_tre=[f"Quinta ({(d+timedelta(days=1)).strftime('%d/%m')})", f"Sexta ({(d+timedelta(days=2)).strftime('%d/%m')})"],
                    detalhes="Feriado na quarta + 2 folgas TRE enforcando quinta e sexta.",
                    is_alta_temporada=False
                ))

    # =========================================================================
    # PARTE 2: RECESSOS ESCOLARES E FÉRIAS COLETIVAS DO CASAL (0 TRE)
    # =========================================================================
    # Réveillon 2026/2027
    adicionar(JanelaUnificada(
        inicio=date(2026, 12, 30) if ano == 2026 else date(ano, 1, 1),
        fim=date(2027, 1, 4) if ano == 2026 else date(ano, 1, 5),
        nome_evento="Réveillon / Férias de Janeiro",
        categoria=JanelaUnificada.CATEGORIA_PURO,
        folgas_tre_gastas=0,
        dias_tre=[],
        detalhes="Recesso de início de ano letivo.",
        is_alta_temporada=True
    ))

    # Recesso Escolar do Meio do Ano (SEEDUC e Prefeituras em Julho)
    adicionar(JanelaUnificada(
        inicio=date(ano, 7, 17),
        fim=date(ano, 7, 25),
        nome_evento="Recesso Escolar de Julho (Casal)",
        categoria=JanelaUnificada.CATEGORIA_PURO,
        folgas_tre_gastas=0,
        dias_tre=[],
        detalhes="Recesso escolar de meio de ano do magistério (livre para Hugo e recesso/férias da esposa).",
        is_alta_temporada=True
    ))

    # =========================================================================
    # PARTE 3: FINS DE SEMANA ATÍPICOS ALAVANCADOS COM TRE (1 a 2 FOLGAS)
    # =========================================================================
    cursor = date(ano, 1, 1)
    while cursor.weekday() != 3:  # Primeira quinta-feira
        cursor += timedelta(days=1)

    while cursor.year == ano:
        qui = cursor
        sex = qui + timedelta(days=1)
        sab = qui + timedelta(days=2)
        dom = qui + timedelta(days=3)
        seg = qui + timedelta(days=4)
        ter = qui + timedelta(days=5)

        # Meses estratégicos de baixa/média temporada (março, abril, maio, junho, agosto, setembro, outubro, novembro)
        if qui.month in (3, 4, 5, 6, 8, 9, 10, 11) and (8 <= qui.day <= 22):
            # A. Quinta a Domingo (4 dias)
            adicionar(JanelaUnificada(
                inicio=qui,
                fim=dom,
                nome_evento="Fim de Semana Alavancado (Qui ➔ Dom)",
                categoria=JanelaUnificada.CATEGORIA_ALAVANCADO_TRE,
                folgas_tre_gastas=2,
                dias_tre=[f"Quinta ({qui.strftime('%d/%m')})", f"Sexta ({sex.strftime('%d/%m')})"],
                detalhes="Saída na quinta-feira aproveitando passagens de contrafluxo.",
                is_alta_temporada=False
            ))

            # B. Sábado a Terça (4 dias)
            adicionar(JanelaUnificada(
                inicio=sab,
                fim=ter,
                nome_evento="Fim de Semana Alavancado (Sáb ➔ Ter)",
                categoria=JanelaUnificada.CATEGORIA_ALAVANCADO_TRE,
                folgas_tre_gastas=2,
                dias_tre=[f"Segunda ({seg.strftime('%d/%m')})", f"Terça ({ter.strftime('%d/%m')})"],
                detalhes="Volta na terça-feira (dia mais barato da aviação comercial).",
                is_alta_temporada=False
            ))

            # C. Sexta a Terça (5 dias)
            adicionar(JanelaUnificada(
                inicio=sex,
                fim=ter,
                nome_evento="Ponte Estendida (Sex ➔ Ter)",
                categoria=JanelaUnificada.CATEGORIA_ALAVANCADO_TRE,
                folgas_tre_gastas=2,
                dias_tre=[f"Segunda ({seg.strftime('%d/%m')})", f"Terça ({ter.strftime('%d/%m')})"],
                detalhes="5 dias contíguos de descanso com retorno na terça econômica.",
                is_alta_temporada=False
            ))

        cursor += timedelta(days=7)

    janelas.sort(key=lambda x: x.inicio)
    return janelas


if __name__ == "__main__":
    todas = obter_janelas_unificadas_ano(2027)
    puras = [j for j in todas if j.folgas_tre_gastas == 0]
    alavancadas = [j for j in todas if j.folgas_tre_gastas > 0]

    print(f"📊 MOTOR DE CALENDÁRIO UNIFICADO (2027):")
    print(f" • Total de Janelas: {len(todas)}")
    print(f" • Janelas 100% PURAS (Feriados, Pontos Facultativos e Recessos): {len(puras)}")
    print(f" • Janelas ALAVANCADAS com TRE (Extensões e Fins de Semana): {len(alavancadas)}")

    print("\n🟢 EXEMPLOS DE JANELAS 100% PURAS:")
    for p in puras[:8]:
        print(f"  - {p.label_amigavel()} | {p.detalhes}")

    print("\n🟡 EXEMPLOS DE JANELAS ALAVANCADAS COM TRE:")
    for a in alavancadas[:8]:
        print(f"  - {a.label_amigavel()} | {a.detalhes}")
