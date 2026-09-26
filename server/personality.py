from __future__ import annotations

"""Personalização real do assistente: nome, personalidade (prompt de
sistema) e preferência de voz. Persistido em disco — não é só cosmético,
o /api/chat usa isso de verdade em toda conversa."""

import json
import threading
from pathlib import Path
from typing import Any, Dict

_DB_PATH = Path(__file__).resolve().parent / 'data' / 'personality.json'
_LOCK = threading.Lock()

_DEFAULTS: Dict[str, Any] = {
    'assistant_name': 'JARVIS',
    'personality_prompt': (
        'Você é o JARVIS, um assistente pessoal direto, educado e prestativo. '
        'Responda em português do Brasil, de forma objetiva.'
    ),
    'voice_provider': 'browser',  # browser | elevenlabs | local
    'voice_id': '',
}


def get_personality() -> Dict[str, Any]:
    with _LOCK:
        if not _DB_PATH.exists():
            return dict(_DEFAULTS)
        try:
            data = json.loads(_DB_PATH.read_text(encoding='utf-8'))
        except Exception:
            return dict(_DEFAULTS)
        merged = dict(_DEFAULTS)
        merged.update({k: v for k, v in data.items() if k in _DEFAULTS})
        return merged


def set_personality(patch: Dict[str, Any]) -> Dict[str, Any]:
    current = get_personality()
    for key in _DEFAULTS:
        if key in patch and patch[key] is not None:
            value = str(patch[key])[:4000] if key == 'personality_prompt' else str(patch[key])[:120]
            current[key] = value
    with _LOCK:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _DB_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding='utf-8')
    return current


def build_system_prompt(override: str | None = None) -> str:
    """Prompt de sistema real usado no /api/chat: nome + personalidade
    configurados pelo usuário, a menos que a chamada mande um `system`
    explícito (esse ainda tem prioridade)."""
    if override:
        return override
    p = get_personality()
    name = p['assistant_name'] or 'JARVIS'
    return f"Seu nome é {name}. {p['personality_prompt']}"
