# Backend v2 (`server/app.py`) — Segurança, personalidade, conectores e Superagente

Este documento cobre só o que foi adicionado de verdade ao backend FastAPI
(`server/app.py`) nesta rodada — nada aqui é enfeite, é tudo endpoint real,
com teste automatizado em `tests/test_security_and_connectors.py`.

## 1. Segurança em pontos críticos

- *Rate limit* em memória (sem Redis) nos endpoints que custam dinheiro/SMS
  ou podem ser abusados: login Google, pedido/verificação de OTP por
  telefone, `/api/chat`, `/api/voice/tts`, WhatsApp, conectores de casa e a
  ponte com o Superagente.
- *Sessões com expiração real*: token de login expira sozinho depois de
  `JARVIS_SESSION_TTL_SECONDS` (7 dias por padrão), em vez de durar pra
  sempre.
- *OTP por SMS*: se `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` /
  `TWILIO_PHONE` estiverem configurados, o código sai por SMS de verdade e
  **nunca** volta na resposta da API. Sem Twilio configurado, cai em modo
  demonstração local (aí sim devolve o código, só pra teste).
- Cabeçalhos de segurança em toda resposta (`X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`).
- CORS configurável via `JARVIS_ALLOWED_ORIGINS` (lista separada por
  vírgula). Padrão `*` pra facilitar uso local/pessoal — trave pro seu
  domínio real em produção.

Variáveis novas:

```bash
JARVIS_ALLOWED_ORIGINS=https://seusite.com
JARVIS_SESSION_TTL_SECONDS=604800
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE=+55...
```

## 2. Personalidade real (nome, tom, voz)

`GET/POST /api/personality` — nome do assistente e o prompt de personalidade
ficam salvos em `server/data/personality.json` e são usados de verdade em
toda chamada de `/api/chat` (a menos que a chamada já mande um `system`
próprio). Campos: `assistant_name`, `personality_prompt`, `voice_provider`,
`voice_id`.

## 3. Conectores customizáveis

`GET/POST /api/connectors`, `DELETE /api/connectors/{id}` — cadastro de
conectores (`home_assistant`, `webhook`, `ntfy`, `custom_api`) com nome, URL
base e token. O token nunca volta em claro pra quem lista — só os últimos 4
caracteres, pra confirmar qual é qual.

### Casa inteligente (Home Assistant)

```bash
HOME_ASSISTANT_URL=http://192.168.1.10:8123
HOME_ASSISTANT_TOKEN=eyJ...   # Long-Lived Access Token, gerado no perfil do HA
```

- `GET /api/home/states` — lista todos os estados/entidades
- `POST /api/home/call` `{domain, service, entity_id}` — ex.:
  `{"domain":"light","service":"turn_on","entity_id":"light.sala"}`

## 4. Ponte real com o Superagente (app + WhatsApp)

`POST /api/superagent/chat` `{"message": "..."}` fala direto com o mesmo
Superagente Base44 que você já usa no app e no WhatsApp — pela Agent API
pública dele.

```bash
SUPERAGENT_API_KEY=...          # gerada no editor do agente (Developer/API Docs)
SUPERAGENT_AGENT_ID=6ab67c8cce89ca33ff6ee7b9   # já vem preenchido com este Superagent
```

Sem `SUPERAGENT_API_KEY`, o endpoint devolve erro 502 explicando o que falta
— não finge que funcionou.

## 5. O que ainda depende de você

- Gerar a `SUPERAGENT_API_KEY` no editor do agente e colocar no ambiente do
  servidor.
- Ter um Home Assistant rodando na sua rede (se quiser casa inteligente de
  verdade) e gerar o Long-Lived Access Token.
- Ligar o Twilio (opcional) se quiser SMS real em vez do modo demonstração.
