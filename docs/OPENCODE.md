# OpenCode — Configuração completa do JARVIS HUD v2

Este repositório está pronto para ser usado com o [OpenCode](https://opencode.ai).

## Estrutura

| Caminho | O que faz |
|---|---|
| `opencode.json` | Configuração principal: provedores, modelos, agentes e permissões |
| `.opencode/agents/` | Agentes especializados (review, security, docs, commit) |
| `.opencode/commands/` | Comandos slash: `/review`, `/audit`, `/test`, `/models`, `/commit` |
| `.opencode/plugins/` | Plugins locais — `jarvis-guard.js` bloqueia leitura de `.env` e segredos |
| `.opencode/rules/` | Regras do projeto lidas por todos os agentes |
| `AGENTS.md` | Instruções gerais para qualquer agente de código |

## Modelos configurados

Cada provedor em `opencode.json` usa endpoint compatível com OpenAI e lê a chave de
uma variável de ambiente (nunca de arquivo commitado):

| Provedor | Variável de ambiente |
|---|---|
| Groq | `GROQ_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |
| Cerebras | `CEREBRAS_API_KEY` |
| Google Gemini | `GEMINI_API_KEY` |
| GitHub Models | `GITHUB_TOKEN` |
| Hugging Face | `HUGGINGFACE_API_KEY` |
| Mistral AI | `MISTRAL_API_KEY` |
| SambaNova | `SAMBANOVA_API_KEY` |
| SiliconFlow | `SILICONFLOW_API_KEY` |
| NVIDIA NIM | `NVIDIA_NIM_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |
| Cohere | `COHERE_API_KEY` |
| Zhipu GLM | `ZHIPU_API_KEY` |
| Alibaba Qwen | `QWEN_API_KEY` |
| Meta Llama API | `LLAMA_API_KEY` |
| Cloudflare Workers AI | `CLOUDFLARE_API_KEY` + `CLOUDFLARE_ACCOUNT_ID` |
| Ollama (local) | nenhuma |

Modelos cobertos: Qwen3, Qwen2.5-Coder, Qwen2.5, DeepSeek-R1, DeepSeek-V3,
DeepSeek-Coder, Llama 3.3/3.2/3.1/4, Mistral 7B, Mixtral, Gemma 3/2, Phi-4/Phi-3,
Command R, Yi, InternLM, GLM-4, MiniCPM, StarCoder2, Code Llama, GPT-OSS e as
variantes Nemotron (Super 49B e Ultra 253B).

## Como usar

1. Exporte as chaves que você tem, por exemplo:
   `export GROQ_API_KEY=... OPENROUTER_API_KEY=...`
2. `npm i -g opencode-ai@latest` (ou `curl -fsSL https://opencode.ai/install | bash`)
3. Na raiz do repositório, rode `opencode`
4. Use `Tab` para alternar entre os agentes primários Build e Plan, `@review`,
   `@security`, `@docs` e `@commit` para invocar subagentes, e `/models` para ver
   o catálogo configurado

## Voz (Fish Audio)

O HUD v3.1 tem motor de voz Fish Audio. Cadastre a chave em Configurações →
Provedores → Fish Audio (ela vai para o cofre local criptografado) ou exporte
`FISH_AUDIO_API_KEY` no servidor. Sem chave, o JARVIS cai automaticamente para a
voz do navegador.

## Segurança

- O repositório é público: **nunca** comite chaves. Use variáveis de ambiente.
- `server/.env.example` lista todas as variáveis suportadas.
- O plugin `jarvis-guard.js` impede o agente de ler `.env` e arquivos de credenciais.
