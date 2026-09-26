from __future__ import annotations

import requests

from server.config import CONFIG


def send_via_evolution(to: str, text: str) -> dict:
    if not (CONFIG.evolution_api_url and CONFIG.evolution_api_key):
        raise RuntimeError('Evolution API is not configured')
    url = f'{CONFIG.evolution_api_url}/message/sendText/{to}'
    headers = {'apikey': CONFIG.evolution_api_key, 'Content-Type': 'application/json'}
    payload = {'text': text}
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()
