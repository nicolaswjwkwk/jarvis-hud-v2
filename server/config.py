from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class AppConfig:
    host: str = field(default_factory=lambda: os.getenv('JARVIS_HOST', '0.0.0.0'))
    port: int = field(default_factory=lambda: int(os.getenv('JARVIS_PORT', '8080')))
    model_url: str = field(default_factory=lambda: os.getenv('JARVIS_MODEL_URL', 'http://127.0.0.1:11434/v1/chat/completions'))
    model_name: str = field(default_factory=lambda: os.getenv('JARVIS_MODEL', 'llama3.2'))
    google_client_id: str = field(default_factory=lambda: os.getenv('GOOGLE_CLIENT_ID', ''))
    google_client_secret: str = field(default_factory=lambda: os.getenv('GOOGLE_CLIENT_SECRET', ''))
    google_redirect_uri: str = field(default_factory=lambda: os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8080/auth/google/callback'))
    twilio_account_sid: str = field(default_factory=lambda: os.getenv('TWILIO_ACCOUNT_SID', ''))
    twilio_auth_token: str = field(default_factory=lambda: os.getenv('TWILIO_AUTH_TOKEN', ''))
    twilio_phone: str = field(default_factory=lambda: os.getenv('TWILIO_PHONE', ''))
    whatsapp_access_token: str = field(default_factory=lambda: os.getenv('WHATSAPP_ACCESS_TOKEN', ''))
    whatsapp_phone_number_id: str = field(default_factory=lambda: os.getenv('WHATSAPP_PHONE_NUMBER_ID', ''))
    whatsapp_verify_token: str = field(default_factory=lambda: os.getenv('WHATSAPP_VERIFY_TOKEN', ''))
    whatsapp_webhook_secret: str = field(default_factory=lambda: os.getenv('WHATSAPP_WEBHOOK_SECRET', ''))
    evolution_api_url: str = field(default_factory=lambda: os.getenv('EVOLUTION_API_URL', 'http://localhost:8081'))
    evolution_api_key: str = field(default_factory=lambda: os.getenv('EVOLUTION_API_KEY', ''))
    openrouter_api_key: str = field(default_factory=lambda: os.getenv('OPENROUTER_API_KEY', ''))

    # ── Voz local (Piper/Kokoro/XTTS) ──
    tts_url: str = field(default_factory=lambda: os.getenv('JARVIS_TTS_URL', 'http://127.0.0.1:5000'))

    # ── Segurança ──
    # Lista separada por vírgula, ex: "https://meusite.com,https://outro.com".
    # "*" (padrão) libera qualquer origem — ok pra uso pessoal/local, mas
    # recomenda-se travar pro domínio real em produção.
    allowed_origins: str = field(default_factory=lambda: os.getenv('JARVIS_ALLOWED_ORIGINS', '*'))
    session_ttl_seconds: int = field(default_factory=lambda: int(os.getenv('JARVIS_SESSION_TTL_SECONDS', str(60 * 60 * 24 * 7))))  # 7 dias

    # ── Ponte com o Superagente Base44 (app + WhatsApp) ──
    superagent_api_key: str = field(default_factory=lambda: os.getenv('SUPERAGENT_API_KEY', ''))
    superagent_agent_id: str = field(default_factory=lambda: os.getenv('SUPERAGENT_AGENT_ID', '6ab67c8cce89ca33ff6ee7b9'))
    superagent_base_url: str = field(default_factory=lambda: os.getenv('SUPERAGENT_BASE_URL', 'https://app.base44.com'))

    # ── Casa inteligente (Home Assistant) ──
    home_assistant_url: str = field(default_factory=lambda: os.getenv('HOME_ASSISTANT_URL', ''))
    home_assistant_token: str = field(default_factory=lambda: os.getenv('HOME_ASSISTANT_TOKEN', ''))

    def cors_origins(self) -> list[str]:
        raw = (self.allowed_origins or '*').strip()
        if raw == '*':
            return ['*']
        return [o.strip() for o in raw.split(',') if o.strip()]


CONFIG = AppConfig()


# ── OTP em memória (demo local) ──────────────────────────────────
import time as _time

_OTP_STORE: dict[str, tuple[str, float]] = {}
_OTP_TTL_SECONDS = 300


def store_otp(phone: str, code: str) -> None:
    """Guarda um código OTP com validade de 5 minutos."""
    _OTP_STORE[phone] = (code, _time.time() + _OTP_TTL_SECONDS)


def verify_otp(phone: str, code: str) -> bool:
    """Confere (e consome) o OTP se ainda estiver válido."""
    record = _OTP_STORE.get(phone)
    if not record:
        return False
    stored, expires_at = record
    if _time.time() > expires_at:
        _OTP_STORE.pop(phone, None)
        return False
    if stored != code:
        return False
    _OTP_STORE.pop(phone, None)
    return True
