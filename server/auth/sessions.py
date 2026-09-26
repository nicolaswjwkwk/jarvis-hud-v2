from __future__ import annotations

import json
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from server.config import CONFIG

_DB_PATH = Path(__file__).resolve().parent.parent / 'data' / 'sessions.json'
_LOCK = threading.Lock()


def _load() -> Dict[str, Any]:
    if not _DB_PATH.exists():
        return {}
    try:
        return json.loads(_DB_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _save(data: Dict[str, Any]) -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def issue_token() -> str:
    return secrets.token_urlsafe(32)


def create_session(user_id: str, provider: str, profile: Optional[Dict[str, Any]] = None) -> str:
    """Cria e persiste a sessão em disco (server/data/sessions.json) para que
    o login continue válido mesmo se o servidor reiniciar. Expira sozinha
    após CONFIG.session_ttl_seconds (7 dias por padrão) — ponto crítico de
    segurança: sessão nunca deve durar pra sempre."""
    token = issue_token()
    now = time.time()
    with _LOCK:
        data = _load()
        data[token] = {
            'user_id': user_id,
            'provider': provider,
            'token': token,
            'profile': profile or {},
            'created_at': now,
            'expires_at': now + CONFIG.session_ttl_seconds,
        }
        _save(data)
    return token


def get_session(token: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        data = _load()
        session = data.get(token)
        if not session:
            return None
        expires_at = session.get('expires_at')
        if expires_at is not None and time.time() > expires_at:
            data.pop(token, None)
            _save(data)
            return None
        return session


def delete_session(token: str) -> None:
    with _LOCK:
        data = _load()
        if token in data:
            del data[token]
            _save(data)


def purge_expired_sessions() -> int:
    """Remove sessões vencidas do disco. Retorna quantas foram removidas."""
    now = time.time()
    removed = 0
    with _LOCK:
        data = _load()
        for token in list(data.keys()):
            expires_at = data[token].get('expires_at')
            if expires_at is not None and now > expires_at:
                data.pop(token, None)
                removed += 1
        if removed:
            _save(data)
    return removed
