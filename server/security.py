from __future__ import annotations

"""Segurança em pontos críticos: limite de tentativas (rate limit) em memória
e cabeçalhos de segurança HTTP. Sem dependências externas — funciona em
qualquer ambiente, mesmo sem Redis."""

import threading
import time
from collections import defaultdict

_LOCK = threading.Lock()
_HITS: dict[str, list[float]] = defaultdict(list)


class RateLimitExceeded(Exception):
    """Levantado quando uma chave (ex.: IP+rota) excede o limite permitido."""

    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f'Limite de requisições excedido. Tente novamente em {retry_after:.0f}s.')


def check_rate_limit(key: str, max_calls: int, window_seconds: float) -> None:
    """Levanta RateLimitExceeded se `key` já bateu `max_calls` na janela.

    Pontos críticos que usam isto: login/OTP por telefone, callback do
    Google, chat com IA e a ponte com o Superagente — tudo que custa
    créditos, manda SMS real ou pode ser usado pra abuso.
    """
    now = time.monotonic()
    with _LOCK:
        hits = _HITS[key]
        cutoff = now - window_seconds
        while hits and hits[0] < cutoff:
            hits.pop(0)
        if len(hits) >= max_calls:
            retry_after = window_seconds - (now - hits[0])
            raise RateLimitExceeded(max(retry_after, 1.0))
        hits.append(now)


def client_key(request, suffix: str) -> str:
    """Chave de limite baseada no IP do cliente (respeita proxy reverso)."""
    ip = request.headers.get('x-forwarded-for', '').split(',')[0].strip()
    if not ip and request.client:
        ip = request.client.host
    return f'{ip or "unknown"}:{suffix}'


SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'no-referrer',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
}
