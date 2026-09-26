# JARVIS Sessions

This backend scaffold adds the real agent hooks needed to support:
- Google login via OAuth
- phone login via OTP
- WhatsApp Cloud API
- optional Evolution API fallback
- model routing to Ollama / OpenAI-compatible / OpenRouter
- tool registry and planner for autonomous tasks

## Run

```bash
cd /path/to/jarvis-hud-v2
python3 -m venv .venv
source .venv/bin/activate
pip install -r server/requirements.txt
cp server/.env.example .env
# edit .env with real values
uvicorn server.app:app --host 0.0.0.0 --port 8080
```

## Security notes

- Never put secrets in JavaScript localStorage.
- Keep credentials on the server only.
- Add rate limiting and a lockout policy for OTP requests.
