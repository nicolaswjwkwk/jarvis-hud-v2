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
