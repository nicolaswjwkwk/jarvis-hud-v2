# Local development notes

The mobile PWA can be served together with the local AI gateway at `http://localhost:8080`:

```bash
python3 server/server.py
```

The gateway serves `jarvis-x.html` as the default page and forwards chat requests to an
OpenAI-compatible local model endpoint. By default it uses Ollama at
`http://127.0.0.1:11434/v1/chat/completions`.

## Mobile use

- Use Chrome, Edge, or Safari for microphone permissions and Web Speech support.
- For a phone accessing a computer over Wi-Fi, start with `JARVIS_HOST=0.0.0.0` and open
  `http://<computer-lan-ip>:8080`.
- Do not expose port 8080 to the public internet: the development gateway has no authentication.
- Install the PWA from the browser's “Add to Home Screen” action.

## Scope of the integration

The existing HUD already contains mobile layout, PWA, voice, local memory, provider selection,
skills, automations, plugins, and WhatsApp UI. This update adds a real local serving/API boundary
without importing proprietary or unrelated desktop source from another project.
