
## 10. Catálogo de extensões e repositórios open source (58 repos, set/2026)

Aba *Modelos* → seção "Extensões & Plugins": grid com busca em tempo real
sobre 58 repositórios open source reais que complementam o JARVIS. Cada card
tem descrição curta e link direto pro GitHub. Categorias:

1. Cérebro local (Ollama, llama.cpp, vLLM, text-generation-webui, LocalAI,
   Jan, GPT4All, LiteLLM, KoboldCpp)
2. Agentes autônomos (LangChain, LangGraph, CrewAI, AutoGPT, BabyAGI, MetaGPT,
   OpenHands, Aider, SuperAGI, browser-use, AgentGPT, OpenCode)
3. Voz real — TTS/STT (Piper, Coqui/XTTS-v2, F5-TTS, Kokoro, Bark,
   whisper.cpp, faster-whisper, RVC, OpenVoice)
4. Automação de fluxo (n8n, Node-RED, Home Assistant, ESPHome, Huginn)
5. Mensagens (Baileys, whatsapp-web.js, Evolution API, venom-bot,
   python-telegram-bot)
6. Navegador (Playwright, Puppeteer, Stagehand)
7. Sem chave de API (SearXNG — busca própria, LibreTranslate — tradução
   própria)
8. Memória vetorial (ChromaDB, Qdrant, FAISS, Weaviate)
9. Ponte com celular/casa (KDE Connect, ntfy, Gotify, Syncthing, Termux)
10. Visão/OCR (Tesseract, EasyOCR, PaddleOCR)
11. Música (OpenTune-Web — player de música web open source)

### Combos "fora da caixa" que valem a pena

- *browser-use + Ollama*: dá pro Agente Autônomo controlar o navegador de
  verdade (comprar algo, preencher formulário, extrair dados) usando um
  modelo 100% local, sem mandar nada pra nuvem.
- *ntfy no celular*: notificação push real e imediata do JARVIS, sem
  depender só do WhatsApp — self-hosted, sem chave, 2 minutos pra configurar.
- *KDE Connect*: o JARVIS podia, no futuro, ler notificações e disparar
  ações no PC direto do celular (e vice-versa), sem precisar de nenhuma nuvem.
- *SearXNG + LibreTranslate*: substitui de vez qualquer API paga de busca ou
  tradução no painel Open Tools — os dois rodam na sua própria máquina.
- *ChromaDB*: dá memória de longo prazo de verdade pro agente (hoje ele só
  guarda notas simples no navegador) — lembra de conversas antigas por
  similaridade semântica.
- *Termux*: se um dia você quiser o backend do JARVIS rodando direto no
  celular (sem depender do PC ligado), é por aqui.

Todos esses são só catálogo/sugestão por enquanto — nenhum está com código
de integração pronto. Se quiser algum rodando de verdade, é só pedir qual
(ex.: "quero o ntfy funcionando" ou "integra o browser-use no Agente").
