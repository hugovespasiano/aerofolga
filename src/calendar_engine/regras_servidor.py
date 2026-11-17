"""
regras_servidor.py — AeroFolga / Vespasiano Labs
Modelagem de perfis dos servidores, regras de lotação (SEEDUC x Barra Mansa),
pontos facultativos e o otimizador de saldo coringa do TRE.
"""

from datetime import date
from typing import List, Dict, Set, Optional
from calendar_engine.feriados_fixos import obter_feriados_ano, mapa_feriados_por_data, Feriado


class StatusDia:
    LIVRE = "LIVRE"
    TRABALHO = "TRABALHO"
    CORINGA_TRE_POSSIVEL = "CORINGA_TRE_POSSIVEL"


class VinculoServidor:
    def __init__(
        self,
        nome: str,
        esfera: str,  # 'municipal' ou 'estadual'
        cidade_lotacao: str,  # 'Barra Mansa', 'Itatiaia', 'Volta Redonda'
        segue_feriado_municipal_lotacao: bool = True,
        segue_ponto_facultativo_municipal: bool = True,
        recessos_escolares: Optional[List[tuple]] = None,  # [(inicio, fim), ...]
        pontos_facultativos_decretados: Optional[Set[date]] = None,
        sabados_letivos: Optional[Set[date]] = None,
    ):
        self.nome = nome
        self.esfera = esfera
        self.cidade_lotacao = cidade_lotacao
        self.segue_feriado_municipal_lotacao = segue_feriado_municipal_lotacao
        self.segue_ponto_facultativo_municipal = segue_ponto_facultativo_municipal
        self.recessos_escolares = recessos_escolares or []
        self.pontos_facultativos_decretados = pontos_facultativos_decretados or set()
        self.sabados_letivos = sabados_letivos or set()

    def esta_livre(self, d: date, feriados_dia: List[Feriado]) -> tuple[bool, str]:
        """
        Retorna (True/False, motivo) indicando se o servidor está liberado do trabalho neste vínculo.
        """
        # Sábado letivo de reposição bloqueia viagem
        if d in self.sabados_letivos:
            return False, f"Bloqueio: Sábado Letivo de Reposição em {self.nome}"

        # Fim de semana convencional
        if d.weekday() in (5, 6):  # Sábado e Domingo
            return True, "Fim de Semana"

        # Recessos escolares (férias / recesso de meio de ano)
        for inicio, fim in self.recessos_escolares:
            if inicio <= d <= fim:
                return True, f"Recesso Escolar ({self.nome})"

        # Feriados Fixos e Móveis
        for f in feriados_dia:
            if f.esfera in ("nacional", "nacional_religioso"):
                return True, f"Feriado Nacional: {f.nome}"
            if f.esfera == "estadual_rj":
                return True, f"Feriado Estadual RJ: {f.nome}"

            # Regra de ouro da SEEDUC: autoriza feriado municipal do local da lotação!
            if self.segue_feriado_municipal_lotacao:
                if f.esfera == "municipal_bm" and self.cidade_lotacao == "Barra Mansa":
                    return True, f"Feriado Municipal de {self.cidade_lotacao}: {f.nome}"
                if f.esfera == "municipal_itatiaia" and self.cidade_lotacao == "Itatiaia":
                    return True, f"Feriado Municipal de {self.cidade_lotacao}: {f.nome}"
                if f.esfera == "municipal_vr" and self.cidade_lotacao == "Volta Redonda":
                    return True, f"Feriado Municipal de {self.cidade_lotacao}: {f.nome}"

        # Pontos Facultativos Decretados
        if d in self.pontos_facultativos_decretados:
            return True, f"Ponto Facultativo Decretado ({self.nome})"

        return False, f"Dia Útil de Trabalho ({self.nome})"


class PerfilCasal:
    def __init__(self, saldo_folgas_tre_hugo: int = 4):
        self.saldo_tre = saldo_folgas_tre_hugo

        # Vínculos do Hugo
        self.vinculo_hugo_itatiaia = VinculoServidor(
            nome="Prefeitura de Itatiaia (Municipal)",
            esfera="municipal",
            cidade_lotacao="Itatiaia",
            segue_feriado_municipal_lotacao=True,
            segue_ponto_facultativo_municipal=True
        )

        self.vinculo_hugo_seeduc = VinculoServidor(
            nome="SEEDUC-RJ (Estadual em Barra Mansa)",
            esfera="estadual",
            cidade_lotacao="Barra Mansa",
            segue_feriado_municipal_lotacao=True,     # SEEDUC segue feriado de Barra Mansa
            segue_ponto_facultativo_municipal=False   # SEEDUC NÃO segue ponto facultativo de Barra Mansa!
        )

        # Vínculo da Esposa
        self.vinculo_esposa_vr = VinculoServidor(
            nome="Prefeitura de Volta Redonda",
            esfera="municipal",
            cidade_lotacao="Volta Redonda",
            segue_feriado_municipal_lotacao=True,
            segue_ponto_facultativo_municipal=True
        )

    def status_dia_casal(self, d: date, feriados_map: Dict[date, List[Feriado]]) -> dict:
        """
        Avalia a situação do dia para o casal:
        - Hugo só está 100% livre se estiver livre em Itatiaia E na SEEDUC.
        - Esposa livre em Volta Redonda.
        - Se a Esposa estiver livre e o Hugo estiver preso em apenas 1 vínculo (ou ambos),
          avalia se 1 dia de folga do TRE pode desbloquear o dia.
        """
        feriados_dia = feriados_map.get(d, [])

        livre_hugo_ita, motivo_ita = self.vinculo_hugo_itatiaia.esta_livre(d, feriados_dia)
        livre_hugo_see, motivo_see = self.vinculo_hugo_seeduc.esta_livre(d, feriados_dia)
        livre_esposa, motivo_esp = self.vinculo_esposa_vr.esta_livre(d, feriados_dia)

        livre_hugo = livre_hugo_ita and livre_hugo_see

        motivos_hugo = []
        if livre_hugo_ita:
            motivos_hugo.append(motivo_ita)
        if livre_hugo_see:
            motivos_hugo.append(motivo_see)

        # Ambos 100% livres
        if livre_hugo and livre_esposa:
            return {
                "data": d,
                "status": StatusDia.LIVRE,
                "hugo_livre": True,
                "esposa_livre": True,
                "requer_tre": False,
                "detalhes": f"Hugo: {'; '.join(motivos_hugo)} | Esposa: {motivo_esp}"
            }

        # Esposa livre, Hugo preso: oportunidade de usar Coringa TRE!
        if livre_esposa and not livre_hugo:
            bloqueio_hugo = []
            if not livre_hugo_ita:
                bloqueio_hugo.append("Trabalho em Itatiaia")
            if not livre_hugo_see:
                bloqueio_hugo.append("Trabalho na SEEDUC (BM)")

            return {
                "data": d,
                "status": StatusDia.CORINGA_TRE_POSSIVEL,
                "hugo_livre": False,
                "esposa_livre": True,
                "requer_tre": True,
                "detalhes": f"Esposa livre ({motivo_esp}), Hugo requer 1 folga TRE para liberar ({', '.join(bloqueio_hugo)})"
            }

        return {
            "data": d,
            "status": StatusDia.TRABALHO,
            "hugo_livre": livre_hugo,
            "esposa_livre": livre_esposa,
            "requer_tre": False,
            "detalhes": "Dia letivo regular"
        }
