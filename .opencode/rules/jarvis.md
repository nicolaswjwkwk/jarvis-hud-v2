# Regras do projeto — JARVIS HUD v2

- Interface em português do Brasil; código e identificadores em inglês.
- Nunca comite chaves de API ou senhas. Use variáveis de ambiente (ver server/.env.example) ou {env:VAR} no opencode.json.
- Frontend é vanilla JS (sem framework), arquivos minificados em js/ — ao editar, preserve o estilo compacto e o IIFE `(function(global){...})(window)`.
- Novos provedores entram no CATALOG em js/providers.js com url, keyUrl, docs e note.
- Servidor é Python (Flask) em server/; testes em tests/ via pytest.
- Commits seguem Conventional Commits em português.
