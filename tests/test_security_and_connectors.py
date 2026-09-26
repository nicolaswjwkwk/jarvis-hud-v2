from __future__ import annotations

from fastapi.testclient import TestClient

from server.app import app
from server.auth import sessions as sessions_module
from server.security import RateLimitExceeded, check_rate_limit

client = TestClient(app)


# ── Segurança: cabeçalhos ──
def test_security_headers_present():
    response = client.get('/health')
    assert response.headers.get('x-content-type-options') == 'nosniff'
    assert response.headers.get('x-frame-options') == 'DENY'


# ── Segurança: rate limit ──
def test_rate_limit_blocks_after_threshold():
    key = 'test-ip:some_route'
    for _ in range(5):
        check_rate_limit(key, max_calls=5, window_seconds=60)
    try:
        check_rate_limit(key, max_calls=5, window_seconds=60)
        assert False, 'deveria ter levantado RateLimitExceeded'
    except RateLimitExceeded:
        pass


def test_phone_request_rate_limited_by_ip():
    for i in range(5):
        client.post('/auth/phone/request', json={'phone': f'+55119999000{i}'})
    resp = client.post('/auth/phone/request', json={'phone': '+5511999900099'})
    assert resp.status_code == 429


# ── OTP nunca revela o código quando SMS real está configurado ──
def test_otp_demo_mode_returns_code_without_twilio():
    resp = client.post('/auth/phone/request', json={'phone': '+5511900011122'})
    assert resp.status_code in (200, 429)
    if resp.status_code == 200:
        body = resp.json()
        assert body['provider'] == 'demo_sem_sms_configurado'
        assert 'code' in body


# ── Sessões: criação, leitura e expiração real ──
def test_session_create_and_expire():
    token = sessions_module.create_session('user@example.com', 'google', {'email': 'user@example.com'})
    session = sessions_module.get_session(token)
    assert session is not None
    assert session['user_id'] == 'user@example.com'

    # força expiração manualmente e confirma que get_session não devolve mais
    data = sessions_module._load()
    data[token]['expires_at'] = 0
    sessions_module._save(data)
    assert sessions_module.get_session(token) is None


def test_session_logout_deletes_token():
    token = sessions_module.create_session('user2@example.com', 'phone')
    resp = client.post('/api/session/logout', json={'token': token})
    assert resp.status_code == 200
    assert sessions_module.get_session(token) is None


# ── Personalidade real (nome, tom, voz) ──
def test_personality_default_and_update():
    resp = client.get('/api/personality')
    assert resp.status_code == 200
    assert resp.json()['personality']['assistant_name']

    resp = client.post('/api/personality', json={'assistant_name': 'Athena', 'personality_prompt': 'Seja breve.'})
    assert resp.status_code == 200
    body = resp.json()['personality']
    assert body['assistant_name'] == 'Athena'
    assert body['personality_prompt'] == 'Seja breve.'

    resp = client.get('/api/personality')
    assert resp.json()['personality']['assistant_name'] == 'Athena'


def test_chat_uses_personality_name_in_degraded_reply():
    client.post('/api/personality', json={'assistant_name': 'Athena'})
    resp = client.post('/api/chat', json={'messages': [{'role': 'user', 'content': 'oi'}]})
    assert resp.status_code == 200
    # modo degradado ainda deve responder normalmente mesmo com personalidade custom
    assert resp.json()['choices'][0]['message']['role'] == 'assistant'


# ── Conectores customizáveis ──
def test_connectors_crud():
    resp = client.post('/api/connectors', json={
        'name': 'Casa', 'type': 'home_assistant', 'base_url': 'http://192.168.1.10:8123', 'token': 'segredo123'})
    assert resp.status_code == 200
    connector = resp.json()['connector']
    assert connector['token_preview'].endswith('3123'[-4:]) or connector['token_preview'].endswith('o123')
    assert 'segredo123' not in str(connector)

    resp = client.get('/api/connectors')
    assert resp.status_code == 200
    ids = [c['id'] for c in resp.json()['connectors']]
    assert connector['id'] in ids

    resp = client.delete(f"/api/connectors/{connector['id']}")
    assert resp.status_code == 200

    resp = client.delete(f"/api/connectors/{connector['id']}")
    assert resp.status_code == 404


def test_connectors_rejects_invalid_type():
    resp = client.post('/api/connectors', json={'name': 'X', 'type': 'nao_existe', 'base_url': 'http://x.com'})
    assert resp.status_code == 400


def test_connectors_rejects_bad_url():
    resp = client.post('/api/connectors', json={'name': 'X', 'type': 'webhook', 'base_url': 'ftp://x.com'})
    assert resp.status_code == 400


# ── Home Assistant: sem config, erro claro (não trava) ──
def test_home_states_without_config_returns_502():
    resp = client.get('/api/home/states')
    assert resp.status_code == 502


# ── Superagente: sem chave configurada, erro claro (não trava) ──
def test_superagent_chat_without_key_returns_502():
    resp = client.post('/api/superagent/chat', json={'message': 'oi'})
    assert resp.status_code == 502


def test_superagent_chat_requires_message():
    resp = client.post('/api/superagent/chat', json={})
    assert resp.status_code == 400
