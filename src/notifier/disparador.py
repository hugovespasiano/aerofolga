"""
disparador.py — AeroFolga / Vespasiano Labs
Disparador de alertas nos canais do casal (Console, Telegram, WhatsApp).
"""

import os
import json
import urllib.request
import urllib.parse
from typing import Optional


class DisparadorAlerta:
    def __init__(
        self,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        whatsapp_api_url: Optional[str] = None,
        whatsapp_api_key: Optional[str] = None,
        whatsapp_numero: Optional[str] = None
    ):
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
                return resp.status == 200
        except Exception as e:
            print(f"⚠️ Erro ao disparar no Telegram: {e}")
            return False

    def enviar_whatsapp(self, mensagem: str) -> bool:
        """Envia para o WhatsApp via Evolution API."""
        if not self.whatsapp_api_url or not self.whatsapp_numero:
            return False

        endpoint = f"{self.whatsapp_api_url.rstrip('/')}/message/sendText/{os.getenv('EVOLUTION_INSTANCE_NAME', 'aerofolga')}"
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
                return resp.status in (200, 201)
        except Exception as e:
            print(f"⚠️ Erro ao disparar no WhatsApp: {e}")
            return False
