"""
disparador.py — AeroFolga / Vespasiano Labs
Disparador de alertas nos canais do casal (Console, Telegram, WhatsApp).
Carrega automaticamente credenciais do arquivo .env.
"""

import os
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional


def carregar_env():
    """Carregador leve e nativo de variáveis do .env sem dependências externas."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ:
                        os.environ[key] = val


class DisparadorAlerta:
    def __init__(
        self,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        whatsapp_api_url: Optional[str] = None,
        whatsapp_api_key: Optional[str] = None,
        whatsapp_numero: Optional[str] = None
    ):
        carregar_env()
        self.telegram_token = telegram_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.whatsapp_api_url = whatsapp_api_url or os.getenv("EVOLUTION_API_URL")
        self.whatsapp_api_key = whatsapp_api_key or os.getenv("EVOLUTION_API_KEY")
        self.whatsapp_numero = whatsapp_numero or os.getenv("WHATSAPP_NUMERO")

    def enviar_console(self, mensagem: str):
        """Imprime a notificação no terminal com formatação limpa."""
        print("\n" + "=" * 55)
        print("📲 DISPARO DE ALERTA NO CONSOLE")
        print("=" * 55)
        print(mensagem)
        print("=" * 55 + "\n")

    def enviar_telegram(self, mensagem: str) -> bool:
        """Envia para o bot do Telegram do casal."""
        if not self.telegram_token or not self.telegram_chat_id:
            return False

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": mensagem,
            "parse_mode": "Markdown"
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    print("✅ Alerta enviado com sucesso para o Telegram!")
                    return True
                return False
        except Exception as e:
            print(f"⚠️ Erro ao disparar no Telegram: {e}")
            return False

    def enviar_whatsapp(self, mensagem: str) -> bool:
        """Envia para o WhatsApp via Evolution API."""
        if not self.whatsapp_api_url or not self.whatsapp_numero:
            return False

        instancia = os.getenv("EVOLUTION_INSTANCE_NAME", "aerofolga")
        endpoint = f"{self.whatsapp_api_url.rstrip('/')}/message/sendText/{instancia}"
        payload = {
            "number": self.whatsapp_numero,
            "text": mensagem
        }

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "apikey": self.whatsapp_api_key or ""
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    print("✅ Alerta enviado com sucesso para o WhatsApp!")
                    return True
                return False
        except Exception as e:
            print(f"⚠️ Erro ao disparar no WhatsApp: {e}")
            return False
