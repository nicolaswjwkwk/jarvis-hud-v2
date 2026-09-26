from __future__ import annotations

"""Conectores customizáveis registrados pelo usuário — hoje cobre casa
inteligente (Home Assistant) e é genérico o bastante pra outros serviços
REST no futuro. Guardado em disco; o token nunca é devolvido em claro pra
quem lista os conectores (só os 4 últimos caracteres, pra confirmar qual é
qual sem expor o segredo)."""

import json
import threading
from pathlib import Path
from typing import Any, Dict, List

_DB_PATH = Path(__file__).resolve().parent.parent / 'data' / 'connectors.json'
_LOCK = threading.Lock()

ALLOWED_TYPES = {'home_assistant', 'webhook', 'ntfy', 'custom_api'}


def _load() -> Dict[str, Dict[str, Any]]:
    if not _DB_PATH.exists():
        return {}
    try:
        return json.loads(_DB_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _save(data: Dict[str, Dict[str, Any]]) -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def _mask(token: str) -> str:
    if not token:
        return ''
    return ('•' * max(len(token) - 4, 0)) + token[-4:]


def list_connectors() -> List[Dict[str, Any]]:
    with _LOCK:
        data = _load()
    out = []
    for cid, c in data.items():
        out.append({
            'id': cid,
            'name': c.get('name', ''),
            'type': c.get('type', ''),
            'base_url': c.get('base_url', ''),
            'token_preview': _mask(c.get('token', '')),
        })
    return out


def get_connector_secret(connector_id: str) -> Dict[str, Any] | None:
    """Uso interno apenas (nunca exposto direto pela API): devolve o registro
    completo, incluindo o token real, pra quem for de fato chamar o serviço."""
    with _LOCK:
        return _load().get(connector_id)


def add_connector(name: str, type_: str, base_url: str, token: str = '') -> Dict[str, Any]:
    if type_ not in ALLOWED_TYPES:
        raise ValueError(f"Tipo de conector inválido. Use um de: {', '.join(sorted(ALLOWED_TYPES))}")
    if not base_url.startswith(('http://', 'https://')):
        raise ValueError('base_url precisa começar com http:// ou https://')
    import secrets
    cid = secrets.token_hex(6)
    record = {'name': name[:80], 'type': type_, 'base_url': base_url.rstrip('/'), 'token': token}
    with _LOCK:
        data = _load()
        data[cid] = record
        _save(data)
    return {'id': cid, 'name': record['name'], 'type': type_, 'base_url': record['base_url'], 'token_preview': _mask(token)}


def delete_connector(connector_id: str) -> bool:
    with _LOCK:
        data = _load()
        if connector_id not in data:
            return False
        del data[connector_id]
        _save(data)
        return True
