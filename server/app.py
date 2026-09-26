from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from server.agent.planner import build_default_plan
from server.auth.google_oauth import build_google_auth_url, exchange_google_code, fetch_google_userinfo
from server.auth.phone_auth import request_phone_otp, verify_phone_otp, status_summary
from server.auth.sessions import create_session, delete_session, get_session
from server.channels.evolution_api import send_via_evolution
from server.channels.whatsapp_cloud import send_whatsapp_message, verify_whatsapp_signature
from server.config import CONFIG
from server.connectors import home_assistant, registry as connectors_registry
from server.connectors.base44_superagent import SuperagentError, send_message as send_superagent_message
from server.personality import build_system_prompt, get_personality, set_personality
from server.security import SECURITY_HEADERS, RateLimitExceeded, check_rate_limit, client_key

app = FastAPI(title='JARVIS Backend', version='0.3.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.cors_origins(),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.middleware('http')
async def security_headers_middleware(request: Request, call_next):
    """Cabeçalhos de segurança em toda resposta — ponto crítico barato de
    proteger (clickjacking, MIME sniffing, permissões do navegador)."""
    response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


def _enforce_rate_limit(request: Request, suffix: str, max_calls: int, window_seconds: float) -> None:
    try:
        check_rate_limit(client_key(request, suffix), max_calls, window_seconds)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


class ChatMessage(BaseModel):
    role: str = Field(default='user')
    content: str = Field(..., min_length=1, max_length=100000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    system: str | None = None


@app.get('/health')
async def health() -> dict:
    return {'ok': True, 'service': 'jarvis-backend', 'status': 'online', 'model_url': CONFIG.model_url, 'model': CONFIG.model_name}


@app.get('/auth/status')
async def auth_status() -> dict:
    return status_summary()


@app.post('/auth/google/start')
async def google_start(request: Request) -> dict:
    _enforce_rate_limit(request, 'google_start', max_calls=10, window_seconds=60)
    try:
        return {'ok': True, 'url': build_google_auth_url()}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _google_popup_html(payload: dict) -> str:
    """Página mínima devolvida no popup do Google: entrega o resultado pro
    JARVIS (via postMessage) e fecha a janela sozinha."""
    body = json.dumps(payload)
    return (
        '<!doctype html><html><body style="background:#0a0f14;color:#eaf6ff;'
        'font-family:sans-serif;display:flex;align-items:center;justify-content:'
        'center;height:100vh;margin:0">'
        '<p>Login concluído. Pode fechar esta janela.</p>'
        '<script>'
        f'window.opener && window.opener.postMessage({{type:"jarvis_google_login",payload:{body}}}, "*");'
        'setTimeout(function(){window.close()}, 600);'
        '</script></body></html>'
    )


@app.get('/auth/google/callback')
async def google_callback(request: Request, code: str | None = None) -> Response:
    _enforce_rate_limit(request, 'google_callback', max_calls=20, window_seconds=60)
    if not code:
        return Response(
            content=_google_popup_html({'ok': False, 'error': 'Código de autorização ausente'}),
            media_type='text/html')
    try:
        token_payload = exchange_google_code(code)
        access_token = token_payload.get('access_token')
        profile = fetch_google_userinfo(access_token)
        session_token = create_session(
            profile.get('email') or profile.get('sub') or 'google-user', 'google', profile)
        return Response(
            content=_google_popup_html({'ok': True, 'session_token': session_token, 'user': profile}),
            media_type='text/html')
    except Exception as exc:
        return Response(
            content=_google_popup_html({'ok': False, 'error': f'Falha no login Google: {exc}'}),
            media_type='text/html')


@app.post('/auth/phone/request')
async def phone_request(request: Request, payload: dict) -> dict:
    # Ponto crítico: pedir OTP custa SMS real (Twilio) — limite por IP além
    # do throttle por telefone que já existe em request_phone_otp.
    _enforce_rate_limit(request, 'phone_request', max_calls=5, window_seconds=600)
    phone = (payload or {}).get('phone')
    if not phone:
        raise HTTPException(status_code=400, detail='Phone is required')
    try:
        return request_phone_otp(str(phone))
    except ValueError as exc:
        raise HTTPException(status_code=429, detail=str(exc))


@app.post('/auth/phone/verify')
async def phone_verify(request: Request, payload: dict) -> dict:
    # Ponto crítico: tentativa de adivinhar o código de 6 dígitos.
    _enforce_rate_limit(request, 'phone_verify', max_calls=10, window_seconds=600)
    phone = (payload or {}).get('phone')
    code = (payload or {}).get('code')
    if not phone or not code:
        raise HTTPException(status_code=400, detail='Phone and code are required')
    try:
        return verify_phone_otp(str(phone), str(code))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@app.post('/api/chat')
async def chat(req: ChatRequest, request: Request) -> dict:
    _enforce_rate_limit(request, 'chat', max_calls=60, window_seconds=60)
    messages = [{'role': item.role, 'content': item.content} for item in req.messages]

    # Personalidade real (nome + tom configurados pelo usuário) entra como
    # system prompt, a menos que a chamada já mande um `system` explícito.
    messages.insert(0, {'role': 'system', 'content': build_system_prompt(req.system)})

    text = req.messages[-1].content if req.messages else 'Olá'
    payload = {
        'model': CONFIG.model_name,
        'messages': messages,
        'stream': False,
        'temperature': 0.7,
    }

    try:
        http_request = urllib.request.Request(
            CONFIG.model_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(http_request, timeout=90) as response:
            response_data = json.loads(response.read().decode('utf-8'))
    except (urllib.error.URLError, TimeoutError):
        return {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': f'Modelo local indisponível no momento. Resposta local: {text}'
                }
            }],
            'degraded': True,
            'plan': build_default_plan(text),
        }

    if not response_data.get('choices'):
        raise HTTPException(status_code=502, detail='Model responded without choices')

    response_data.setdefault('plan', build_default_plan(text))
    return response_data


@app.post('/api/whatsapp/webhook')
async def whatsapp_webhook(request: Request) -> dict:
    raw = await request.body()
    signature = request.headers.get('X-Hub-Signature-256', '')
    if CONFIG.whatsapp_webhook_secret and not verify_whatsapp_signature(raw, signature.replace('sha256=', '')):
        raise HTTPException(status_code=401, detail='Invalid WhatsApp signature')
    try:
        payload = json.loads(raw.decode('utf-8')) if raw else {}
    except Exception:
        payload = {}
    return {'ok': True, 'received': payload}


@app.post('/api/whatsapp/send')
async def whatsapp_send(request: Request, payload: dict) -> dict:
    _enforce_rate_limit(request, 'whatsapp_send', max_calls=30, window_seconds=60)
    to = (payload or {}).get('to')
    text = (payload or {}).get('text')
    if not to or not text:
        raise HTTPException(status_code=400, detail='Recipient and text are required')
    if CONFIG.whatsapp_access_token and CONFIG.whatsapp_phone_number_id:
        return send_whatsapp_message(to, text)
    if CONFIG.evolution_api_url and CONFIG.evolution_api_key:
        return send_via_evolution(to, text)
    raise HTTPException(status_code=400, detail='No WhatsApp provider configured')


@app.get('/api/session')
async def get_session_info(token: str) -> dict:
    session = get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail='Invalid session token')
    return {'ok': True, 'session': session}


@app.post('/api/session/logout')
async def logout(payload: dict) -> dict:
    token = str((payload or {}).get('token', ''))
    if token:
        delete_session(token)
    return {'ok': True}


# ── Voz real open source (Piper / Kokoro / XTTS via servidor local) ──
@app.post('/api/voice/tts')
async def voice_tts(request: Request, payload: dict) -> Response:
    """Recebe {"text": "..."} e devolve o áudio gerado pelo servidor TTS local
    (Piper, Kokoro, XTTS-v2, F5-TTS). Configuração: JARVIS_TTS_URL."""
    _enforce_rate_limit(request, 'voice_tts', max_calls=30, window_seconds=60)
    text = str((payload or {}).get('text', ''))[:2000]
    if not text:
        raise HTTPException(status_code=400, detail="Campo 'text' obrigatório.")
    tts_url = CONFIG.tts_url.rstrip('/')
    req = urllib.request.Request(
        tts_url,
        data=json.dumps({'text': text}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST')
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            audio = resp.read()
            ctype = resp.headers.get('Content-Type', 'audio/wav')
        return Response(content=audio, media_type=ctype)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f'Servidor de voz local offline ({exc}). Ligue o Piper/Kokoro em {tts_url}')


# ── Personalidade real (nome, tom, voz) ──
@app.get('/api/personality')
async def personality_get() -> dict:
    return {'ok': True, 'personality': get_personality()}


@app.post('/api/personality')
async def personality_set(payload: dict) -> dict:
    return {'ok': True, 'personality': set_personality(payload or {})}


# ── Conectores customizáveis (casa inteligente e outros) ──
@app.get('/api/connectors')
async def connectors_list() -> dict:
    return {'ok': True, 'connectors': connectors_registry.list_connectors()}


@app.post('/api/connectors')
async def connectors_add(payload: dict) -> dict:
    payload = payload or {}
    try:
        record = connectors_registry.add_connector(
            name=str(payload.get('name', '')),
            type_=str(payload.get('type', '')),
            base_url=str(payload.get('base_url', '')),
            token=str(payload.get('token', '')),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {'ok': True, 'connector': record}


@app.delete('/api/connectors/{connector_id}')
async def connectors_delete(connector_id: str) -> dict:
    ok = connectors_registry.delete_connector(connector_id)
    if not ok:
        raise HTTPException(status_code=404, detail='Conector não encontrado')
    return {'ok': True}


# ── Casa inteligente: Home Assistant real ──
@app.get('/api/home/states')
async def home_states(request: Request) -> dict:
    _enforce_rate_limit(request, 'home_states', max_calls=30, window_seconds=60)
    try:
        states = home_assistant.list_states(CONFIG.home_assistant_url, CONFIG.home_assistant_token)
    except home_assistant.HomeAssistantError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {'ok': True, 'states': states}


@app.post('/api/home/call')
async def home_call(request: Request, payload: dict) -> dict:
    _enforce_rate_limit(request, 'home_call', max_calls=30, window_seconds=60)
    payload = payload or {}
    domain = str(payload.get('domain', ''))
    service = str(payload.get('service', ''))
    entity_id = str(payload.get('entity_id', ''))
    if not (domain and service and entity_id):
        raise HTTPException(status_code=400, detail='domain, service e entity_id são obrigatórios')
    try:
        result = home_assistant.call_service(CONFIG.home_assistant_url, CONFIG.home_assistant_token, domain, service, entity_id)
    except home_assistant.HomeAssistantError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {'ok': True, 'result': result}


# ── Ponte real com o Superagente (Base44) — app + WhatsApp já é o mesmo agente ──
@app.post('/api/superagent/chat')
async def superagent_chat(request: Request, payload: dict) -> dict:
    _enforce_rate_limit(request, 'superagent_chat', max_calls=20, window_seconds=60)
    text = str((payload or {}).get('message', '')).strip()
    if not text:
        raise HTTPException(status_code=400, detail='Campo "message" obrigatório.')
    try:
        reply = send_superagent_message(CONFIG.superagent_base_url, CONFIG.superagent_agent_id, CONFIG.superagent_api_key, text)
    except SuperagentError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {'ok': True, 'reply': reply}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('server.app:app', host=CONFIG.host, port=CONFIG.port, reload=False)
