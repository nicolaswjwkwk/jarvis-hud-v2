# Modelos Open Source Locais — Guia JARVIS

Como rodar IA 100% open source na sua própria máquina e conectar ao JARVIS.
Nenhum desses roda dentro do navegador: são servidores locais que o site chama
pela rede (igual ao Ollama). Recomendado: PC com placa de vídeo (GPU), pelo
menos 8 GB de RAM para os modelos pequenos.

> Permissão geral concedida pelo usuário (set/2026): integrar tudo que for open
> source, sem pedir confirmação, até ele pedir para parar.

---

## 1. Ollama — cérebro do JARVIS (JÁ INTEGRADO)

Cérebro de conversa, roda em CPU fraca.

```bash
# instalar (Windows/Linux/Mac): https://ollama.com/download
ollama pull llama3.2
ollama serve          # sobe em http://127.0.0.1:11434
```

O backend do JARVIS (`server/app.py`) já chama o Ollama em `/api/chat`.
Se estiver offline, responde em modo degradado.

Variáveis de ambiente do backend:

```bash
JARVIS_MODEL_URL=http://127.0.0.1:11434/v1/chat/completions
JARVIS_MODEL=llama3.2
```

---

## 2. OpenVoice — clonagem de voz open source

Repo: https://github.com/myshell-ai/OpenVoice

Gera voz clonada localmente, sem pagar ElevenLabs.

```bash
git clone https://github.com/myshell-ai/OpenVoice
cd OpenVoice
pip install -e .
python -m openvoice.app --port 5000   # sobe UI/API em http://127.0.0.1:5000
```

Depois de rodar, aponte a chave de voz do JARVIS para o servidor local:

```bash
# backend: rotear /api/voice/tts -> OpenVoice
JARVIS_VOICE_URL=http://127.0.0.1:5000
```

Status: PENDENTE — precisa de um endpoint `/api/voice/tts` no backend para
fazer a ponte. Quando o servidor OpenVoice estiver rodando na sua máquina,
peça ao agente para implementar a ponte.

---

## 3. OpenOmni — modelo multimodal (texto + voz)

Repo: https://github.com/OpenOmni/OpenOmni

Assistente que fala e ouve, estilo GPT-4o, open source. Pesado: GPU com 24 GB
de VRAM para o modelo completo (versão pequena roda com menos).

```bash
git clone https://github.com/OpenOmni/OpenOmni
cd OpenOmni
pip install -r requirements.txt
# seguir o README deles para baixar os pesos
```

Status: DOCUMENTADO — integrar exige GPU dedicada. O caminho prático é expor
o modelo num endpoint compatível com OpenAI
(`/v1/chat/completions`) e apontar `JARVIS_MODEL_URL` para ele.

---

## 4. Alternativas leves (sem GPU)

1. **Whisper.cpp** — transcrição de voz local (CPU): https://github.com/ggml-org/whisper.cpp
2. **Piper TTS** — voz local rápida, roda até num Raspberry Pi: https://github.com/rhasspy/piper
3. **Web Speech API** — já embutida no JARVIS X (voz do navegador, zero instalação)

---

## Resumo do stack open source do JARVIS

| Peça | Projeto | Estado |
|---|---|---|
| Cérebro | Ollama (llama3.2) | ✅ integrado |
| Voz no navegador | Web Speech API | ✅ integrado |
| Voz premium | OpenVoice | ⏳ guia pronto |
| Multimodal | OpenOmni | ⏳ guia pronto |
| Transcrição | whisper.cpp | 📄 documentado |
| TTS leve | Piper | 📄 documentado |
| 30 ferramentas | Open Tools Arsenal | ✅ integrado |

---

## 5. Modelos open/free adicionados ao seletor (set/2026)

| Provedor | Modelos | Como usar |
|---|---|---|
| OpenCode Zen | Nemotron 3 Ultra, Ling 3.0 Flash Fin, Muse Spark 1.3 | Configurações → Servidor de IA → OpenCode Zen |
| OpenRouter (free) | Ling 3.0 Flash Fin, Nemotron 3 Ultra/3.5 Lightning, Muse Spark 1.3, DeepSeek R1 | slugs `:free`, chave grátis em openrouter.ai |
| AI/ML API | Space Bunny Alpha (stealth, 1M ctx) | api.aimlapi.com |
| Xiaomi MiMo | MiMo-V2.6-Flash (1M tokens, multimodal) | mimo.mi.com Token Plan |
| NVIDIA NIM | Nemotron 3 Ultra, Nemotron 3.5 Lightning | build.nvidia.com |

## 6. Voz open source (substituem OpenVoice/OpenOmni)

| Projeto | Uso | Repo |
|---|---|---|
| Piper TTS | voz leve, PC fraco | https://github.com/rhasspy/piper |
| Coqui XTTS-v2 | clonagem de voz local | https://github.com/coqui-ai/TTS |
| F5-TTS | voz clonada alta qualidade PT-BR | https://github.com/SWivid/F5-TTS |
| Kokoro TTS | TTS rápido para agentes | https://github.com/hexgrad/kokoro |
| whisper.cpp | transcrição offline (ouvido) | https://github.com/ggml-org/whisper.cpp |

Todos podem expor um endpoint HTTP local e serem chamados pelo backend
FastAPI (mesmo padrão do Ollama).

## 7. Agente Autônomo (novo)

Menu *Agente* no JARVIS X. Recebe um objetivo, planeja os passos e executa:
- WhatsApp real via backend (Evolution API) ou link wa.me + QR
- Abrir apps no celular (deep links: WhatsApp, ligação, mapas, YouTube, Instagram, GitHub, e-mail, Spotify)
- Pesquisa aberta (Wikipédia) e notificação por voz
- Cérebro: o modelo conectado nas Configurações (qualquer provedor open acima) ou modo local com regras

---

## 8. Voz REAL no JARVIS (set/2026)

A voz do navegador é só o plano B. Pra voz real open source:

1. Ligue um servidor TTS local na sua máquina (ex.: Piper, Kokoro, XTTS-v2)
2. Ligue o backend FastAPI com a variável `JARVIS_TTS_URL` apontando pra ele
   (padrão http://127.0.0.1:5000)
3. No site: Configurações → campo "Backend do JARVIS" → URL do backend → salvar

Ordem de prioridade do speak(): ElevenLabs (se tiver chave) → servidor local
open source (Piper/Kokoro/XTTS) → voz do navegador.

A barra de modelos do chat agora lista os modelos REAIS do catálogo
(agrupados por provedor). Os perfis fake "JARVIS X PRO/FAST/CREATIVE" e o
seletor de vozes decorativo (nomes tipo "Marin", "Cedar"...) foram removidos —
não faziam nada de verdade, só mudavam texto na tela.

---

## 9. Por que o login com Google não redireciona (e como resolver de verdade)

O Google só aceita redirecionar o login pra `http://localhost` ou pra um
domínio com HTTPS real. Ele NUNCA aceita IPs de rede local (tipo
`192.168.1.5`), então se o navegador do celular está em outro aparelho que o
PC onde o backend roda, o Google recusa o redirecionamento — não é um bug do
JARVIS, é regra de segurança do próprio Google.

Solução real e gratuita: um serviço de túnel que dá um endereço HTTPS público
de verdade pro seu backend local, sem precisar de chave de API paga. Existem
várias opções open source pra isso (ex.: um túnel Cloudflare "quick tunnel",
que não exige cadastro pro modo rápido). Passo a passo:

1. Rode o backend do JARVIS normalmente na sua máquina (sobe em
   `http://127.0.0.1:8080`).
2. Abra um túnel HTTPS apontando pra essa porta local — isso te devolve uma
   URL pública do tipo `https://algumacoisa.exemplo.com`.
3. No Google Cloud Console → Credenciais → seu Client ID → Authorized
   redirect URIs, adicione: `https://algumacoisa.exemplo.com/auth/google/callback`
4. No servidor, defina a variável de ambiente antes de rodar:
   `GOOGLE_REDIRECT_URI=https://algumacoisa.exemplo.com/auth/google/callback`
5. No JARVIS, em Configurações → Backend do JARVIS, cole essa mesma URL base
   (`https://algumacoisa.exemplo.com`) — ela passa a valer pra login Google,
   WhatsApp e voz real, tudo junto.

URLs de túneis do plano gratuito costumam mudar quando você reinicia o túnel —
repita os passos 3 a 5 quando isso acontecer. Se quiser uma URL fixa, alguns
provedores de túnel oferecem isso numa conta grátis.
