from __future__ import annotations

import hmac
from typing import Any, Dict

import requests

from server.config import CONFIG


def verify_whatsapp_signature(raw_body: bytes, signature: str) -> bool:
    secret = CONFIG.whatsapp_webhook_secret.encode('utf-8')
    expected = hmac.new(secret, raw_body, digestmod='sha256').hexdigest()
    return hmac.compare_digest(signature or '', expected)


def send_whatsapp_message(to: str, text: str) -> Dict[str, Any]:
    if not (CONFIG.whatsapp_access_token and CONFIG.whatsapp_phone_number_id):
        raise RuntimeError('WhatsApp Cloud API is not configured')
    url = f'https://graph.facebook.com/v17.0/{CONFIG.whatsapp_phone_number_id}/messages'
    headers = {'Authorization': f'Bearer {CONFIG.whatsapp_access_token}', 'Content-Type': 'application/json'}
    payload = {
        'messaging_product': 'whatsapp',
        'to': to,
        'type': 'text',
        'text': {'body': text},
    }
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()
