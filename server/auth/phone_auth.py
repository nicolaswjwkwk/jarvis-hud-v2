from __future__ import annotations

import random
import time

from server.auth.sessions import create_session
from server.config import CONFIG, verify_otp, store_otp

# Throttle simples por número: no máx. 3 códigos a cada 10 minutos, pra não
# deixar alguém spamar SMS real (e gastar créditos Twilio) pro mesmo telefone.
_REQUEST_LOG: dict[str, list[float]] = {}
_MAX_REQUESTS = 3
_WINDOW_SECONDS = 600


def generate_code() -> str:
    return str(random.randint(100000, 999999))


def _send_via_twilio(phone: str, code: str) -> bool:
    """Envia o código por SMS real via Twilio, se configurado. Devolve True
    se enviou de verdade, False se não há credenciais (modo demo)."""
    if not (CONFIG.twilio_account_sid and CONFIG.twilio_auth_token and CONFIG.twilio_phone):
        return False
    import requests

    url = f'https://api.twilio.com/2010-04-01/Accounts/{CONFIG.twilio_account_sid}/Messages.json'
    resp = requests.post(
        url,
        data={'To': phone, 'From': CONFIG.twilio_phone, 'Body': f'Seu código JARVIS: {code}'},
        auth=(CONFIG.twilio_account_sid, CONFIG.twilio_auth_token),
        timeout=15,
    )
    resp.raise_for_status()
    return True


def request_phone_otp(phone: str) -> dict:
    if not phone or len(phone) < 8:
        raise ValueError('Phone number is invalid')

    now = time.time()
    hits = [t for t in _REQUEST_LOG.get(phone, []) if now - t < _WINDOW_SECONDS]
    if len(hits) >= _MAX_REQUESTS:
        raise ValueError('Muitos códigos pedidos pra este número. Espere um pouco e tente de novo.')
    hits.append(now)
    _REQUEST_LOG[phone] = hits

    code = generate_code()
    store_otp(phone, code)

    sent_real_sms = _send_via_twilio(phone, code)
    if sent_real_sms:
        # Ponto crítico de segurança: nunca devolve o código quando o SMS
        # real saiu — só quem recebeu o telefone sabe o código.
        return {'ok': True, 'phone': phone, 'provider': 'twilio'}

    # Sem Twilio configurado: modo demonstração local, deixa explícito.
    return {
        'ok': True,
        'phone': phone,
        'provider': 'demo_sem_sms_configurado',
        'code': code,
        'aviso': 'Nenhum SMS real foi enviado. Configure TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_PHONE para envio real.',
    }


def verify_phone_otp(phone: str, code: str) -> dict:
    if not verify_otp(phone, code):
        raise ValueError('Invalid or expired OTP')
    session_token = create_session(phone, 'phone')
    return {'ok': True, 'token': session_token, 'provider': 'phone'}


def status_summary() -> dict:
    return {
        'google_configured': bool(CONFIG.google_client_id and CONFIG.google_client_secret),
        'twilio_configured': bool(CONFIG.twilio_account_sid and CONFIG.twilio_auth_token and CONFIG.twilio_phone),
        'whatsapp_configured': bool(CONFIG.whatsapp_access_token and CONFIG.whatsapp_phone_number_id),
        'evolution_configured': bool(CONFIG.evolution_api_url and CONFIG.evolution_api_key),
        'superagent_configured': bool(CONFIG.superagent_api_key and CONFIG.superagent_agent_id),
        'home_assistant_configured': bool(CONFIG.home_assistant_url and CONFIG.home_assistant_token),
    }
