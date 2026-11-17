"""
extrator_visual.py — AeroFolga / Vespasiano Labs
Módulo de ingestão de calendários escolares e diários oficiais via PDF ou Foto.
Lê resoluções da SEEDUC, calendários escolares municipais e gera o JSON estruturado.
"""

import json
from pathlib import Path
from datetime import date
from typing import Dict, Any, Optional


SCHEMA_CALENDARIO_ESCOLAR = {
    "ano": 2026,
    "ente": "SEEDUC-RJ",
    "recessos_escolares": [
        {"nome": "Recesso de Meio de Ano (Julho)", "inicio": "2026-07-13", "fim": "2026-07-24"},
        {"nome": "Férias Escolares Fim de Ano", "inicio": "2026-12-23", "fim": "2026-12-31"}
    ],
    "pontos_facultativos_previstos": [
        {"nome": "Quarta-feira de Cinzas", "data": "2026-02-18"},
        {"nome": "Emenda de Corpus Christi", "data": "2026-06-05"}
    ],
    "sabados_letivos": [
        {"nome": "Sábado Letivo Reposição 1º Trimestre", "data": "2026-04-18"}
    ]
}


def carregar_calendario_json(caminho_arquivo: str) -> Dict[str, Any]:
    """Carrega um arquivo de calendário estruturado."""
    path = Path(caminho_arquivo)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de calendário não encontrado: {caminho_arquivo}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_calendario_json(dados: Dict[str, Any], caminho_destino: str):
    """Salva o calendário processado na pasta de dados."""
    path = Path(caminho_destino)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"✅ Calendário salvo com sucesso em: {path}")


def template_prompt_extracao_visual(tipo_documento: str = "calendario_escolar") -> str:
    """
    Retorna o prompt padrão enviado ao Gemini Vision para analisar fotos ou PDFs de calendários.
    """
    return f"""
Você é o extrator oficial de calendários do AeroFolga.
Analise a imagem/PDF deste documento ({tipo_documento}).
Identifique todas as legendas de cores e datas:
1. Recessos escolares e férias (datas de início e fim).
2. Pontos facultativos previstos ou decretados.
3. Sábados letivos (dias de reposição que bloqueiam fins de semana).

Responda ESTRITAMENTE em formato JSON compatível com o schema:
{{
  "ano": 2026,
  "ente": "Nome da Prefeitura ou SEEDUC",
  "recessos_escolares": [
    {{"nome": "Descrição", "inicio": "AAAA-MM-DD", "fim": "AAAA-MM-DD"}}
  ],
  "pontos_facultativos_previstos": [
    {{"nome": "Descrição", "data": "AAAA-MM-DD"}}
  ],
  "sabados_letivos": [
    {{"nome": "Descrição", "data": "AAAA-MM-DD"}}
  ]
}}
"""
