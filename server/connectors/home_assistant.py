from __future__ import annotations

"""Conector real de casa inteligente: fala com a API REST do Home Assistant
(open source, self-hosted). Precisa de HOME_ASSISTANT_URL + um Long-Lived
Access Token gerado no próprio Home Assistant (Perfil → Segurança)."""

import json
import urllib.error
import urllib.request
from typing import Any


class HomeAssistantError(RuntimeError):
    pass


def _request(base_url: str, token: str, path: str, method: str = 'GET', body: dict | None = None) -> Any:
    if not base_url or not token:
        raise HomeAssistantError('Home Assistant não configurado (falta URL ou token).')
    url = base_url.rstrip('/') + path
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return json.loads(raw.decode('utf-8')) if raw else {}
    except urllib.error.HTTPError as exc:
        raise HomeAssistantError(f'Home Assistant respondeu {exc.code}: {exc.reason}') from exc
    except urllib.error.URLError as exc:
        raise HomeAssistantError(f'Não consegui alcançar o Home Assistant em {base_url}: {exc.reason}') from exc


def list_states(base_url: str, token: str) -> list[dict]:
    return _request(base_url, token, '/api/states')


def call_service(base_url: str, token: str, domain: str, service: str, entity_id: str) -> Any:
    """Ex.: domain='light', service='turn_on', entity_id='light.sala'."""
    return _request(base_url, token, f'/api/services/{domain}/{service}', method='POST', body={'entity_id': entity_id})
