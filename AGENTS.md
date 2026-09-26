# AGENTS.md

Instruções para agentes de código trabalhando neste repositório.

O projeto é o JARVIS HUD v2: uma interface de assistente pessoal (jarvis-x.html) com
backend opcional em Python (server/), múltiplos provedores de IA (js/providers.js),
síntese de voz (js/voice.js) e cofre de credenciais (js/secure.js).

Diretrizes gerais:
- Leia .opencode/rules/jarvis.md antes de alterar qualquer arquivo.
- Configuração do OpenCode: opencode.json (provedores e modelos) e .opencode/
  (agentes, comandos, plugins e regras).
- Segredos ficam em variáveis de ambiente, nunca em código.

## Rodar no Base44 (preview)

- Projeto 100% estático (HTML/CSS/JS puro, sem build). A entrada é `jarvis-x.html`
  (`index.html` faz redirect). Servido por `python3 -m http.server` no compose.
- O frontend funciona standalone com um motor de intenções embutido ("núcleo local").
  Provedores de IA (Groq, OpenRouter, etc.) são opcionais — as chaves ficam no cofre
  do navegador (`js/secure.js`), não no backend.
- O backend Python em `server/` é opcional (proxy de modelos, auth, WhatsApp).
  Não é necessário para o preview.
- Para rodar: `docker compose -f docker-compose.base44.yml up -d` → porta 3000.
- Sem credenciais externas necessárias para o preview.
