"""
vigilante.py — AeroFolga / Vespasiano Labs
Agente de Vigilância de Preços e Análise de Sazonalidade:
1. Compara preço atual com o histórico de baixa/alta temporada e meses mais baratos.
2. Monitora se uma passagem já barata caiu ainda mais de preço.
3. Evita spam: se o preço se mantiver igual ou subir, não reenvia alerta repetido.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, Optional


class VigilantePrecos:
    def __init__(
        self,
        caminho_historico: str = "data/historico_menor_preco.json",
        caminho_referencia: str = "data/tabela_referencia.json"
    ):
        base_dir = Path(__file__).parent.parent.parent
        self.caminho_historico = base_dir / caminho_historico
        self.caminho_referencia = base_dir / caminho_referencia

        self.historico = self._carregar_json(self.caminho_historico)
        self.referencia = self._carregar_json(self.caminho_referencia)

    def _carregar_json(self, path: Path) -> Dict[str, Any]:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _salvar_historico(self):
        self.caminho_historico.parent.mkdir(parents=True, exist_ok=True)
        with open(self.caminho_historico, "w", encoding="utf-8") as f:
            json.dump(self.historico, f, indent=2, ensure_ascii=False)

    def avaliar_contexto_historico(self, destino: str, preco_atual: float, is_alta_temporada: bool = True) -> Dict[str, Any]:
        """
        Avalia se o preço atual é uma oportunidade real ou se já foi mais barato no ano.
        Sem complexidade: compara com o piso de alta e o piso anual de baixa temporada.
        """
        ref = self.referencia.get(destino, {})
        if not ref:
            return {
                "veredicto": "Sem base histórica",
                "detalhe": "Destino sem histórico cadastrado",
                "meses_baratos": "N/A"
            }

        piso_alta = ref.get("piso_alta_temporada", 700)
        piso_baixa = ref.get("piso_baixa_temporada", 300)
        preco_tipico = ref.get("preco_medio_tipico", 1000)
        meses_baratos = ref.get("meses_mais_baratos", "Baixa temporada")

        piso_alvo = piso_alta if is_alta_temporada else piso_baixa

        if preco_atual <= piso_alvo:
            veredicto = "🔥 EXCEPCIONAL (Piso Histórico)"
        elif preco_atual <= preco_tipico * 0.8:
            veredicto = "✅ MUITO BOM (Abaixo do Típico)"
        else:
            veredicto = "⚠️ NORMAL / ALTO"

        return {
            "veredicto": veredicto,
            "piso_alta": piso_alta,
            "piso_baixa": piso_baixa,
            "preco_tipico": preco_tipico,
            "meses_baratos": meses_baratos,
            "comentario": ref.get("comentario", "")
        }

    def auditar_queda_preco(
        self,
        origem: str,
        destino: str,
        data_ida: str,
        data_volta: str,
        preco_atual: float
    ) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Verifica se o preço é inédito ou se caiu mais em relação à última varredura.
        Retorna: (deve_alertar, motivo_alerta, preco_anterior)
        """
        chave = f"{origem}_{destino}_{data_ida}_{data_volta}"
        registro_anterior = self.historico.get(chave)

        agora_iso = datetime.now().isoformat()

        if registro_anterior is None:
            # Primeiro registro da rota
            self.historico[chave] = {
                "menor_preco": preco_atual,
                "primeira_descoberta": agora_iso,
                "ultima_verificacao": agora_iso,
                "ultimo_alerta_enviado": preco_atual
            }
            self._salvar_historico()
            return True, "NOVA_OPORTUNIDADE", None

        menor_anterior = registro_anterior.get("menor_preco", preco_atual)
        ultimo_alertado = registro_anterior.get("ultimo_alerta_enviado", menor_anterior)

        # Atualiza última verificação
        registro_anterior["ultima_verificacao"] = agora_iso

        # SE O PREÇO CAIU MAIS EM RELAÇÃO AO QUE JÁ TINHA SIDO AVISADO:
        if preco_atual < ultimo_alertado:
            diferenca = ultimo_alertado - preco_atual
            registro_anterior["menor_preco"] = preco_atual
            registro_anterior["ultimo_alerta_enviado"] = preco_atual
            self._salvar_historico()
            return True, f"QUEDA_PRECO (-R$ {diferenca:.0f})", ultimo_alertado

        # Se o preço for igual ou maior, silencia (evita flood)
        self._salvar_historico()
        return False, "PRECO_ESTAVEL_OU_MAIOR", menor_anterior
