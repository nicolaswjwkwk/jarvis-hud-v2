from __future__ import annotations

"""Ponte real com o Superagente (Base44) — o mesmo agente que você já usa no
app e no WhatsApp passa a responder também dentro do JARVIS, pelo endpoint
/api/superagent/chat. Usa a Agent API pública do Base44:
https://app.base44.com/api/agents/<agent_id>

Precisa de duas variáveis de ambiente:
  SUPERAGENT_API_KEY  -> gerada no editor do agente (Developer/API Docs)
  SUPERAGENT_AGENT_ID -> id do app do agente (o Superagent padrão já vem
                         preenchido: 6ab67c8cce89ca33ff6ee7b9)
"""

import json
import urllib.error
import urllib.request
from typing import Any


class SuperagentError(RuntimeError):
    pass


def _call(base_url: str, path: str, api_key: str, method: str = 'GET', body: dict | None = None) -> Any:
    url = base_url.rstrip('/') + path
    if '?' in url:
        url += f'&api_key={api_key}'
    else:
        url += f'?api_key={api_key}'
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={'Content-Type': 'application/json', 'api_key': api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return json.loads(raw.decode('utf-8')) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='ignore')
        raise SuperagentError(f'Superagente respondeu {exc.code}: {detail[:300]}') from exc
    except urllib.error.URLError as exc:
        raise SuperagentError(f'Não consegui alcançar o Superagente ({exc.reason}).') from exc


def send_message(base_url: str, agent_id: str, api_key: str, text: str) -> str:
    """Manda `text` pra conversa padrão do agente e devolve o texto da resposta."""
    if not agent_id or not api_key:
        raise SuperagentError(
            'Ponte com o Superagente não configurada. Defina SUPERAGENT_API_KEY '
            '(gerada no editor do agente) e, se quiser, SUPERAGENT_AGENT_ID.')
    agents_path = f'/api/agents/{agent_id}'

    conversation = _call(base_url, f'{agents_path}/conversations/default', api_key, method='POST', body={})
    conversation_id = conversation.get('id') or conversation.get('conversation_id')
    if not conversation_id:
        raise SuperagentError('Não recebi um id de conversa válido do Superagente.')

    reply = _call(
        base_url, f'{agents_path}/conversations/{conversation_id}/messages', api_key,
        method='POST', body={'content': text, 'role': 'user'})

    content = reply.get('content') or reply.get('message') or reply.get('text')
    if isinstance(content, dict):
        content = content.get('content') or content.get('text')
    return str(content or 'Superagente respondeu, mas sem texto legível.')
