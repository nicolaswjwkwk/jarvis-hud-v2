# JARVIS Mobile Local Server

This directory contains a dependency-free local gateway for the mobile-first PWA.

## Start

1. Install and start [Ollama](https://ollama.com/), then pull a model:

   ```bash
   ollama pull llama3.2
   ```

2. From the repository root, run:

   ```bash
   python3 server/server.py
   ```

3. Open <http://localhost:8080> on the device running the server. The health check is
   available at <http://localhost:8080/health>.

## Configuration

The defaults are deliberately local-only:

- `JARVIS_HOST` — bind address, default `127.0.0.1`
- `JARVIS_PORT` — HTTP port, default `8080`
- `JARVIS_MODEL_URL` — OpenAI-compatible local endpoint, default Ollama on port `11434`
- `JARVIS_MODEL` — default model, `llama3.2`

For a phone on the same Wi-Fi network, bind explicitly and use the computer's LAN address
in the phone browser:

```bash
JARVIS_HOST=0.0.0.0 python3 server/server.py
```

Only do this on a trusted private network and restrict port 8080 with your firewall. This
minimal server has no authentication and must not be exposed to the public internet.

## API

- `GET /health`
- `GET /api/config`
- `POST /v1/chat/completions`
- `POST /api/chat` (alias)

The POST endpoints accept an OpenAI-compatible JSON body and proxy it to the configured local
model server. No API keys are required or persisted by this gateway.
