# J.A.R.V.I.S. HUD · v2 — Superagente

> Verificação automática: `python3 quickcheck.py` (sintaxe, estrutura, assertivas
> funcionais e alcance das URLs publicadas).

Interface HUD futurista, escrita do zero em HTML/CSS/JS puro (sem framework, sem dependência
de build), agora operando como **frontend de um superagente**: backend de modelos, agente de
código, autonomia com rotinas e memória, canal de WhatsApp, painel de administração com
segurança em nível de aplicação e sistema de plugins.

> Versão anterior (v1, apenas assistente): `webpages/jarvis-hud/`.

---

## Índice

1. [Como rodar localmente](#1-como-rodar-localmente)
2. [Arquitetura](#2-arquitetura)
3. [Backend de IA (endpoint, chave, modelo, timeout, retry)](#3-backend-de-ia)
4. [Catálogo de modelos e fallback automático](#4-catálogo-de-modelos-e-fallback-automático)
5. [Voz configurável](#5-voz-configurável)
6. [Painel do administrador e segurança](#6-painel-do-administrador-e-segurança)
7. [Autonomia, agendamentos e WhatsApp](#7-autonomia-agendamentos-e-whatsapp)
8. [Plugins, manifest e hooks](#8-plugins-manifest-e-hooks)
9. [Central de controle](#9-central-de-controle)
10. [Atalhos de teclado](#10-atalhos-de-teclado)
11. [Personalização da aparência](#11-personalização-da-aparência)
12. [Solução de problemas](#12-solução-de-problemas)

---

## 1. Como rodar localmente

Não há etapa de build. Basta servir a pasta por HTTP — **não abra o arquivo direto com
`file://`**, porque os módulos usam `fetch` e a Web Speech API exige origem segura
(`http://localhost` conta como segura).

```bash
cd webpages/jarvis-hud_v2
python3 -m http.server 8000
# abra http://localhost:8000
```

Alternativas:

```bash
npx serve -l 8000 .          # Node
php -S localhost:8000        # PHP
```

Publicado (URL permanente — GitHub Pages, sincronizado com o repo):
`https://nicolaswjwkwk.github.io/jarvis-hud-v2/`

> Publicação antiga (static.teamily.ai), desativada — guardada aqui caso precise reativar:
> `https://static.teamily.ai/sites/ba3c057a-b74e-4e0d-8093-d3d62ece5e5f/webpages/jarvis-hud_v2/index.html`

**Navegadores.** O reconhecimento de voz usa a Web Speech API: funciona em **Chrome, Edge e
Safari**. O **Firefox** não a implementa — a interface detecta a ausência, avisa no microfone e
segue operando por texto normalmente. A síntese de voz tem suporte bem mais amplo.

**Permissão de microfone.** Concedida na primeira vez que você ativa a escuta (botão ou `Ctrl+J`).

---

## 2. Arquitetura

Cada componente vive no próprio arquivo e conversa por um **store reativo** (`JARVIS_State`,
com `on` / `onAny` / `patch` / `emit`). Não há estado global solto.

### Núcleo herdado da v1

| Arquivo | Papel |
|---|---|
| `js/config.js` | **Configuração central** — tudo se ajusta aqui |
| `js/utils.js` | DOM, tempo, texto, ruído procedural |
| `js/state.js` | Store reativo, persistência, publicação de tópicos |
| `js/orb.js` | Orbe canvas: anéis de arcos, ticks, barras radiais, partículas |
| `js/charts.js` | Gráfico multicanal + sparklines dos subsistemas |
| `js/voice.js` | Web Speech API: reconhecimento, síntese, perfis de voz |
| `js/assistant.js` | Motor de intenções (14 famílias) + roteador do superagente |
| `js/chat.js` | Conversa, digitação progressiva, persistência |
| `js/widgets.js` | Relógio, clima, telemetria, subsistemas, avisos, feed |
| `js/palette.js` | Paleta de comandos (`Ctrl+K`) |
| `js/main.js` | Orquestrador: boot, atalhos, pipeline de comandos |

### Módulos novos

| Arquivo | Papel |
|---|---|
| `js/secure.js` | **Primitivas criptográficas**: PBKDF2, AES-GCM, SHA-256 salgado, TOTP (RFC 6238), cofre de segredos |
| `js/auth.js` | Usuários, papéis, sessão com expiração, 2FA (WebAuthn + TOTP), bloqueio, auditoria |
| `js/providers.js` | Catálogo de modelos (locais, nuvem, open source), disponibilidade, fallback |
| `js/backend.js` | Cliente OpenAI-compatível: timeout, retry com backoff, roteamento e cadeia |
| `js/codeagent.js` | Agente de código: copiloto (sugerir/revisar/explicar) e autônomo (multi-etapa) |
| `js/automations.js` | Agendamentos, rotinas, memória de longo prazo, pesquisa e resumos |
| `js/whatsapp.js` | Ponte WhatsApp: 4 backends, fila, retry, resposta automática |
| `js/plugins.js` | Registro de plugins, manifest, hooks, permissões, aprovação |
| `js/control.js` | Central de controle + painel do administrador + autenticação |
| `css/control.css` | Estilos de toda a camada nova (usa os tokens de `theme.css`) |

### Ordem de carregamento

```
config → utils → state → secure → providers → backend → automations → whatsapp
       → codeagent → plugins → auth → control → orb → charts → voice
       → assistant → chat → widgets → palette → main
```

`main.js` é sempre o último. Se você inserir um módulo novo, respeite esta ordem.

---

## 3. Backend de IA

Toda configuração vive em `js/config.js`, no bloco `backend`.

```js
backend: {
  mode: 'auto',            // 'auto' | 'local' | 'cloud'
  url: '',                 // endpoint próprio (opcional)
  key: '',                 // NUNCA coloque a chave aqui — use o cofre (aba Modelos)
  model: '',
  timeoutMs: 45000,        // aborta a chamada após este tempo
  retry: {
    attempts: 3,           // tentativas por provedor
    baseDelayMs: 600,      // espera = baseDelay × 2^tentativa (com jitter)
    maxDelayMs: 8000
  },
  stream: false,           // true habilita leitura incremental
  temperature: 0.7,
  maxTokens: 1200,
  systemPrompt: '...',     // instrução de sistema do assistente
  fallbackChain: ['groq', 'openrouter-free', 'nvidia-nim', ...]  // ver §4
}
```

**Modos**

| Modo | Comportamento |
|---|---|
| `auto` | Usa o provedor ativo; se falhar, desce a cadeia de fallback; fecha no núcleo embutido |
| `local` | Só o núcleo de intenções embutido — zero rede, zero custo |
| `cloud` | Exige provedor remoto; se nenhum estiver disponível, informa a falha |

### Endpoint próprio

Aceita qualquer servidor que fale o formato OpenAI (`/chat/completions`) **ou** um endpoint
simples que devolva `{ "reply": "..." }`. Configure na **aba Modelos → “Backend próprio”** ou em
`backend.url`. Quando preenchido, ele tem prioridade, com a cadeia de fallback como reserva.

Se você já tinha um backend apontado em `api.url` (chave herdada da v1), ela continua sendo
lida pelo motor de intenções para compatibilidade. **Prefira `backend.url`.**

### Testar a comunicação de ponta a ponta

Três caminhos, todos equivalentes:

- Botão **TESTAR PONTA A PONTA** na aba *Modelos*;
- paleta `Ctrl+K` → *Testar conexão com o modelo*;
- digitar `testar conexão`.

O resultado aparece no painel de conexão (modo, provedor, modelo, latência, rota, chamadas e
falhas) e no canal de conversa. O mesmo indicador é a **pílula do cabeçalho** (`NÚCLEO LOCAL` /
`GROQ 420 ms` / `FALHA`), clicável para abrir o painel de modelos.

### Autenticação das chaves

Chaves **nunca** ficam em texto puro no código nem no `localStorage` em claro: são cifradas com
AES-256-GCM no cofre (§6). O fluxo é: autenticar como administrador → aba *Modelos* → **CADASTRAR
CHAVE** → o valor é cifrado e a chave só existe em memória enquanto a sessão estiver aberta.

---

## 4. Catálogo de modelos e fallback automático

`js/providers.js` traz o catálogo completo, dividido em três famílias.

### Locais (sem chave, sem custo)

| Provedor | Como ativar |
|---|---|
| **Ollama** | `ollama serve` — o Jarvis detecta em `http://localhost:11434` |
| **LM Studio** | Inicie o servidor local em `http://localhost:1234/v1` |
| **Jan** | `http://localhost:1337/v1` |
| **llama.cpp / text-generation-webui** | aponte a URL base na aba Modelos |
| **vLLM** | `http://localhost:8000/v1` |
| **GPT4All** | `http://localhost:4891/v1` |

Rodando local, você tem um modelo de graça, offline e privado. É o caminho recomendado para uso
intensivo.

### Camada gratuita (nuvem / open source)

| Provedor | Camada gratuita | Onde obter a chave |
|---|---|---|
| **Groq** | tier gratuito generoso, latência muito baixa | console.groq.com |
| **OpenRouter** | modelos `:free` sem custo | openrouter.ai/keys |
| **NVIDIA NIM** | créditos gratuitos para desenvolvedor | build.nvidia.com |
| **Google AI Studio** | tier gratuito do Gemini | aistudio.google.com |
| **Cerebras** | tier gratuito, inferência rápida | cloud.cerebras.ai |
| **SambaNova** | tier gratuito com modelos abertos de 70B | cloud.sambanova.ai/apis |
| **Mistral** | tier gratuito (`la plateforme`) | console.mistral.ai |
| **GitHub Models** | gratuito com conta GitHub | github.com/marketplace/models |
| **Hugging Face** | Inference API gratuita | huggingface.co/settings/tokens |
| **Kluster.ai** | tier gratuito para modelos abertos | platform.kluster.ai |
| **Zhipu GLM** | tier gratuito (`glm-4-flash`) | open.bigmodel.cn |
| **Cohere** | chave de avaliação (`Trial Key`) | dashboard.cohere.com |
| **Together / Fireworks / Hyperbolic / Novita** | créditos iniciais gratuitos | ver `keyUrl` de cada cartão |

### Pagos (com chave/token)

OpenAI, Anthropic, DeepSeek, xAI (Grok), Perplexity, Moonshot (Kimi), Qwen (DashScope) — todos
no mesmo catálogo, com o mesmo padrão de seleção e fallback. Os gratuitos por créditos
(Together, Fireworks, Hyperbolic, Novita, DeepSeek, NVIDIA NIM) entram aqui quando o saldo
inicial acaba.

> O catálogo é **autodescritivo**: cada cartão na aba *Modelos* mostra `docs`, `keyUrl`, o rótulo
da chave esperada e uma nota sobre o regime de uso. Nenhum provedor é fictício.

### Seleção do modelo ativo

Aba **Modelos** → botão **USAR** no cartão do provedor, escolhendo o modelo na lista ao lado.
Cada cartão mostra o **estado de disponibilidade**: `PRONTO` (respondeu), `SEM CHAVE`,
`SEM RESPOSTA`, `ERRO`. O botão **TESTAR** sonda o provedor individualmente; **LISTAR DO
SERVIDOR** consulta o catálogo real de um servidor local (Ollama/LM Studio) e **VARRER
PROVEDORES** sonda todos os já configurados de uma vez.

### Fallback automático

A cadeia é uma lista ordenada em `config.js → backend.fallbackChain`. O roteador tenta na
ordem e **desce um degrau** a cada falha: sem chave, sem crédito, limite atingido, timeout ou
rede fora. O núcleo de intenções embutido fecha a cadeia — ou seja, **o Jarvis responde mesmo
sem nenhum provedor**, mantendo o mesmo padrão de operação. A ordem da cadeia é editável na aba
*Modelos*, com o estado de cada degrau visível.

O filtro **GRÁTIS** no topo do catálogo isola só os provedores com camada gratuita — útil para
montar uma cadeia de custo zero.

---

## 5. Voz configurável

Voz **ligada por padrão** (`voice.autoSpeak: true`). Perfis prontos em `config.js → voice.profiles`:

| Perfil | Caráter |
|---|---|
| `nucleo` | sóbrio, ritmo normal — padrão |
| `tatico` | mais rápido e agudo, para operação intensa |
| `executivo` | pausado e grave, para relatórios |
| `bilíngue` | síntese em inglês (útil para conteúdo técnico) |
| `silencioso` | volume zero, apenas texto |

Cada perfil define **idioma, voz fixa (opcional), velocidade (`rate`), tom (`pitch`), volume e
palavras de ativação**.

### Trocar de perfil

- Central de controle (`Ctrl+Shift+C`) → aba **Voz** → clique no cartão do perfil;
- por comando: `perfil de voz tático`.

### Ajuste fino

Na mesma aba: controle deslizante de **velocidade** (0,5×–2×), **tom** (0,4–1,8), **volume**
(0–100 %), **idioma** de síntese e **voz específica** do sistema (lista todas as instaladas no
SO, com nome e idioma). O botão **OUVIR AMOSTRA** aplica na hora.

- **Falar as respostas automaticamente** — liga/desliga a fala (`Ctrl+M` faz o mesmo).
- A voz fixada no perfil tem prioridade sobre a escolha automática por idioma.
- Para vozes em português de melhor qualidade, instale os pacotes de fala do sistema operacional.

### Palavras de ativação

`config.js → voice.wakeWords` (padrão `["jarvis", "ei jarvis"]`). Diga *“Jarvis, que horas são”*
que a fala é capturada já em modo comando.

---

## 6. Painel do administrador e segurança

### Credencial inicial — leia isto primeiro

A conta inicial é:

| Campo | Valor |
|---|---|
| Login | `admin` |
| E-mail | o informado na especificação do projeto |
| Senha | a senha provisória definida na instalação |

> **A senha provisória já está gravada apenas como hash PBKDF2-SHA256 (210.000 iterações +
> sal aleatório de 32 bytes).** Nenhum arquivo deste projeto contém a senha em texto puro,
> e ela é irrecuperável a partir dos arquivos entregues. O e-mail também não é guardado em
> claro: só o SHA-256 salgado, com uma máscara para exibição (`nm***@gmail.com`).
>
> **Troque a senha no primeiro acesso.** O painel exibe um aviso persistente enquanto a
> credencial provisória estiver ativa.

### Trocar a senha (você, administrador)

`Ctrl+Shift+C` → aba **Segurança** → **Trocar a minha senha**. Informe a senha atual e a nova
(mínimo 14 caracteres, com medidor de entropia ao vivo). O botão **GERAR SENHA FORTE** cria 24
caracteres aleatórios.

Alternativa por linha de comando, dentro do navegador (console do DevTools):

```js
// troca a própria senha
await JARVIS_Auth.changeOwnPassword('senha-atual', 'nova-senha-forte')

// redefine a de outro usuário (exige sessão de administrador)
await JARVIS_Auth.setPassword('id-do-usuario', 'nova-senha')
```

### Cadastrar novas pessoas

`Ctrl+Shift+A` → aba **Usuários** → seção *Cadastrar novo usuário*: login, nome, e-mail
(opcional), papel e senha inicial (há gerador). Marque **exigir troca no primeiro acesso** para
que a pessoa defina a própria senha.

O administrador pode, por usuário: **trocar o papel**, **redefinir a senha**, **ativar/desativar**,
**revogar o 2FA** e **remover**.

Alternativa por código:

```js
await JARVIS_Auth.createUser({
  login: 'maria', name: 'Maria', email: 'maria@exemplo.com',
  role: 'operator', password: 'senha-forte-aqui', mustChange: true
})
```

### Papéis e permissões

Definidos em `config.js → security.roles`:

| Papel | Alcance |
|---|---|
| `admin` | tudo (`*`) — único que abre o painel ADM |
| `operator` | uso do chat, voz, automações, plugins, canal |
| `viewer` | leitura e conversa |
| `autonomous` | operador + agente autônomo e agendamentos |

As permissões são checadas na interface (`Auth.guard(...)`) e no roteador de intenções.

### Autenticação em duas etapas

Dois fatores **independentes**, configuráveis por conta:

1. **Impressão digital / biometria** (WebAuthn) — o cadastro aceita **apenas o dedo/dispositivo
   registrado**; qualquer outra credencial é recusada pelo próprio autenticador. Requer hardware
   compatível (leitor no celular/notebook) e HTTPS ou `localhost`. Se o navegador não suportar,
   o botão aparece desabilitado com explicação.
2. **Código no celular** (TOTP, RFC 6238) — o painel mostra o segredo em grupos de 4 dígitos;
   cadastre no Google Authenticator, Authy ou 1Password e confirme com um código gerado.

Há ainda a **senha local** e o **e-mail** (usado como identificador de recuperação, guardado
com hash). Com `security.require2FA` ligado, o login pede senha **e** um dos fatores.

### Cofre de credenciais

Todas as chaves de API e tokens do canal ficam num cofre **AES-256-GCM**, cuja chave-mestra é
derivada da senha do usuário (PBKDF2, 120.000 iterações) e **só existe em memória** — recarregar
a página tranca o cofre. Há botões para trancar na hora e para apagar o cofre inteiro. A aba
*Credenciais* ainda aceita **segredos livres** (qualquer token que um plugin ou rotina precise),
pelo nome.

### Trilha de auditoria

Cada evento relevante é registrado de forma imutável com data, ação, detalhe, autor e papel:
login aceito/negado, bloqueio, uso do cofre, gestão de usuários, abertura do painel ADM,
ativação de plugin e envios pelo canal. Visível na aba **Auditoria** (e por comando:
`auditoria`), com exportação e expurgo.

### Política de segurança ajustável

Aba **Política**: iterações do PBKDF2, tentativas antes do bloqueio, duração do bloqueio,
expiração da sessão ociosa, tamanho mínimo de senha e quais fatores de 2FA aceitar.

Padrões: **210.000 iterações** (recomendação OWASP para PBKDF2-SHA256), **5 tentativas**,
bloqueio de **5 minutos**, sessão de **30 minutos**, senha de **14 caracteres**.

### Proteção contra tentativas

Cinco senhas erradas bloqueiam o login por 5 minutos (contagem por usuário, com resposta em
tempo constante para não vazar informação por diferença de tempo).

### O que **não** é garantido

O cofre e o hash protegem contra leitura casual e contra quem tem a máquina em mãos, mas esta é
uma aplicação **de navegador**: um script malicioso rodando na mesma origem teria acesso ao
`localStorage` cifrado, ainda que sem a chave-mestra em memória. Para um limite mais rígido,
hospede a interface em HTTPS, use uma origem dedicada e considere mover a verificação para um
servidor seu — o módulo `auth.js` foi escrito para permitir essa troca sem alterar a interface.

---

## 7. Autonomia, agendamentos e WhatsApp

### Rotinas e agendamentos

Quatro tipos de gatilho:

| Gatilho | Exemplo em linguagem natural |
|---|---|
| Intervalo | *“criar rotina a cada 30 min verificar a telemetria”* |
| Diário | *“criar rotina diariamente às 08:00 resumir as notícias”* |
| Uma vez | *“criar rotina uma vez daqui a 20 minutos”* (via painel) |
| Palavra-chave | *“ao digitar ‘relatório’”* |

Ações disponíveis: **notificar e falar**, **apenas falar**, **publicar no canal**, **pesquisar na
web**, **gerar resumo**, **registrar na memória** e **enviar por WhatsApp**.

A aba **Automações** mostra cada rotina com gatilho, número de execuções, próxima execução
prevista, e os botões EXECUTAR / PAUSAR / REMOVER. O histórico traz as últimas execuções com
origem e resultado. Também funciona por texto: `listar rotinas`, `executar rotina <nome>`.

As rotinas são verificadas por um agendador que roda dentro da página — portanto **executam
enquanto a interface estiver aberta**. Para execução contínua, use um gatilho do sistema
(`cron`) apontando para a mesma URL, ou mantenha a aba aberta.

### Memória de longo prazo

Captura automática de frases como *“lembre-se que…”*, *“eu prefiro…”*, *“meu objetivo é…”*;
gravação manual na aba **Memória** (tipos: `fact`, `preference`, `task`, `person`, `event`);
**busca** com pontuação de relevância; e injeção automática do contexto relevante no prompt
quando o assunto casa. Registros têm peso e contagem de usos; é possível esquecer um item ou
expurgar tudo. Comandos: `lembre-se que …`, `o que você sabe sobre …`, `minhas memórias`.

### Pesquisa e resumos com fontes abertas

`pesquisar <assunto>` consulta **Wikipédia, Hacker News e DuckDuckGo Instant Answer** — todas
sem chave de API — e devolve um resumo com as fontes citadas. `resuma isso` sintetiza a conversa
recente. Se houver um modelo configurado, o resumo é gerado por ele; caso contrário, por
extrativa local.

### WhatsApp

Quatro backends, do mais simples ao mais controlado:

| Backend | Custo | Observação |
|---|---|---|
| **wa.me / link direto** | grátis | envia pelo cliente do usuário; sem automação de recebimento |
| **CallMeBot** | grátis | API simples de envio; ótima para alertas pessoais |
| **Evolution API** | grátis (auto-hospedado) | WhatsApp Web não-oficial, com recebimento |
| **WhatsApp Cloud API (Meta)** | pago por conversa | oficial, estável, para produção |

As credenciais de cada backend (token, instância, `phone_number_id`) são gravadas **no cofre
cifrado**, pela aba **Canal** — nunca em arquivo.

Salvaguardas implementadas: **lista branca de números** (`whatsapp.allowedNumbers`),
**confirmação obrigatória antes do envio** (quando ligada, nada sai sem sua aprovação),
**fila com tentativas**, normalização de número com DDI e **mascaramento do destinatário** nos
registros e na auditoria.

Envio por texto: `whatsapp para +5511999999999 : sua mensagem` — depois `confirmar envio`.
Resposta automática por regras de casamento de texto; sem regra que case, o próprio assistente
responde (quando `autoReply` está ligado).

### Chaves de API pagas e degradação para o gratuito

Modelos pagos e gratuitos convivem no mesmo catálogo e no mesmo padrão de operação. Quando um
provedor pago falha por **crédito esgotado, chave inválida, limite de uso ou indisponibilidade**,
o roteador desce a cadeia e chega automaticamente a uma opção gratuita ou local. Você acompanha
o degrau em uso no painel de conexão (campo **ROTA**) e nos contadores de chamadas/falhas.

---

## 8. Plugins, manifest e hooks

Um plugin é um objeto com manifest que pode adicionar **intenções de conversa**, **comandos na
paleta**, **hooks** de reescrita, **painéis próprios** na central de controle e **ferramentas**
ao agente autônomo.

```js
{
  id: 'meu-plugin',
  name: 'Meu Plugin',
  version: '1.0.0',
  author: 'seu-nome',
  description: 'O que ele faz, em uma frase.',
  permissions: ['chat.use'],          // ver lista abaixo
  intents: [
    { pattern: /^minha saudação$/i, run: () => 'Olá, operador.' }
  ],
  hooks: {
    'command.after': (text) => text + '\n\n— via Meu Plugin',
    'palette.register': ({ commands }) => commands.push({
      icon: '◈', label: 'Ação do Meu Plugin', run: () => S.emit('toast', 'feito')
    })
  },
  panels: [
    { id: 'painel', label: 'Meu Painel', render: (host, api) => { host.textContent = 'conteúdo' } }
  ],
  tools: [
    { name: 'minha-ferramenta', label: 'Minha ferramenta', run: async (args) => ({ ok: true, output: 'feito' }) }
  ],
  setup(api) { /* chamado na ativação */ }
}
```

### Hooks disponíveis

`config.js → plugins.hooks` — os **12 hooks** que o registro publica:

| Hook | Quando dispara |
|---|---|
| `boot` | ao subir o núcleo |
| `command.before` | antes de interpretar o que o operador enviou |
| `command.after` | depois de produzir a resposta |
| `intent.register` | ao registrar intenções próprias de conversa |
| `provider.register` | ao injetar um provedor de modelo no catálogo |
| `tool.register` | ao publicar ferramentas para o agente autônomo |
| `ui.panel` | ao montar painéis extras na central de controle |
| `palette.register` | ao adicionar comandos à paleta (**Ctrl+K**) |
| `assistant.notify` | ao publicar avisos do assistente |
| `keyword.check` | ao avaliar palavras-chave/gatilhos |
| `log` | ao escrever uma linha no registro de eventos |
| `shutdown` | ao encerrar |

A aba *Plugins* lista cada hook e quantos plugins estão ligados nele. Hooks **livres**
(sem plugin) apenas não fazem nada — nunca quebram o fluxo principal.

### Permissões

`net.fetch`, `storage.read`, `storage.write`, `state.read`, `state.write`, `vault.read`,
`notify`, `dom.inject`. Um plugin só recebe o que declarar no manifest **e** for aprovado pelo
administrador; `vault.read` sempre exige o cofre aberto por senha.

### Como instalar

Aba **Plugins** → *Instalar plugin*: preencha o identificador, clique **USAR MODELO** para partir
de um esqueleto, cole o objeto e clique **REGISTRAR PLUGIN**.

**Plugins externos ficam pendentes** até que o administrador os **APROVE** — um plugin não
aprovado não executa. Plugins incluídos de fábrica já vêm aprovados e há um **exemplo funcional
embarcado** (comando na paleta, hook de reescrita, painel próprio e uma ferramenta) que serve de
referência. Cada plugin tem contador de execuções e de erros, e pode ser **desativado**,
**revogado** ou **desinstalado** sem afetar o resto.

Plugins são interpretados com escopo isolado, sem acesso direto ao objeto global, e um erro
dentro de um plugin é capturado sem derrubar a interface.

---

## 9. Central de controle

`Ctrl+Shift+C` (ou o botão ⚙ no cabeçalho, ou `Ctrl+K` → *Central de controle*). Nove abas:

| Aba | O que faz |
|---|---|
| **Modelos** | canal, modo, cadeia de fallback, catálogo completo, chaves, backend próprio |
| **Código** | modo do agente, geração, revisão, explicação, execução isolada, planos |
| **Automações** | criação e gestão de rotinas, histórico de execuções |
| **Memória** | registros de longo prazo, busca, tipos, expurgo |
| **Voz** | perfis, velocidade, tom, volume, idioma, voz do sistema, amostra |
| **Canal** | ponte de WhatsApp, credenciais, envio, fila, resposta automática |
| **Plugins** | registro, aprovação, hooks, instalador, permissões |
| **Segurança** | sessão, troca de senha, segundo fator, atividade recente |
| **Aparência** | paletas de acento, comportamento, resumo do sistema, exportações |

Plugins ativos podem acrescentar abas próprias no fim da lista.

### Agente de código

**Modo copiloto** — sugere, revisa e explica; nada é executado sem você.
**Modo autônomo** — planeja em múltiplos passos e executa, pedindo aprovação no que é sensível.

A revisão cobre 13 classes de risco (credencial embutida, SQL concatenado, `eval`, uso de
`innerHTML`, comparação frouxa, laço sem guarda, entre outras) com nota de 0 a 100 e correção
sugerida por achado. A verificação sintática usa o próprio motor do navegador para JavaScript e
uma análise de delimitadores para as demais linguagens. A **execução isolada** roda JavaScript
em escopo separado, capturando o console sem tocar na página. Planos multi-etapa mostram cada
passo com estado (pendente / executando / concluído / falhou) e permitem aprovar ou cancelar.

Comandos: `modo copiloto`, `modo autônomo`, `gerar código …`, `revisar código`, `explicar código`,
`executar código`, `exportar código`, `planeje …`, `aprovar plano`.

---

## 10. Atalhos de teclado

| Atalho | Ação |
|---|---|
| `Ctrl` `K` | paleta de comandos |
| `Ctrl` `Shift` `C` | central de controle |
| `Ctrl` `Shift` `M` | painel de modelos |
| `Ctrl` `Shift` `A` | painel do administrador |
| `Ctrl` `Shift` `L` | autenticação / cofre |
| `Ctrl` `J` | ativar / encerrar escuta |
| `Ctrl` `I` | focar o console |
| `Ctrl` `M` | silenciar resposta falada |
| `Ctrl` `L` | limpar a conversa |
| `Ctrl` `H` | modo discreto |
| `Ctrl` `/` | ajuda |
| `Alt` `1`–`4` | paleta de acento |
| `Esc` | cancelar escuta / fechar sobreposições (na ordem) |
| `↑` `↓` `Enter` | navegar e executar na paleta |

---

## 11. Personalização da aparência

`config.js → ui.accents` define os esquemas; a aba **Aparência** aplica e mostra o atalho de cada
um. O acento é uma variável CSS (`--accent`, `--accent-rgb`, `--accent-deep`), então trocar a
paleta repinta todo o HUD — inclusive os painéis novos, que só usam tokens.

Para criar um acento próprio, acrescente um item a `ui.accents` e a regra correspondente em
`css/theme.css`:

```css
html[data-accent="magenta"] { --accent:#ff3ea5; --accent-rgb:255,62,165; --accent-deep:#a8136a; }
```

A aba **Aparência** também exporta o **estado completo** em JSON (aparência, voz, backend,
modelos, automações, memória, plugins, canal) e restaura os padrões.

---

## 12. Solução de problemas

**A interface abre mas nada responde.**
Confirme que está servindo por HTTP (`python3 -m http.server 8000`) e não por `file://`.
Abra o console do DevTools: erros de carregamento indicam caminho errado de módulo.

**“SEM CHAVE” no provedor.**
Autentique-se como administrador (`Ctrl+Shift+L`), abra *Modelos*, clique **CADASTRAR CHAVE** ao
lado do provedor e cole a chave. Ela vai para o cofre cifrado.

**O modelo responde devagar ou falha.**
Veja o painel de conexão: **LATÊNCIA** alta, **ROTA** em `fallback` ou contador de **FALHAS**
subindo. Aumente `backend.timeoutMs`, reduza `maxTokens`, ou troque o `mode` para `local`.

**A voz não sai.**
Verifique o volume do sistema e o botão do cabeçalho (não pode estar em mudo). A lista de vozes
vem do sistema operacional: se estiver vazia, faltam pacotes de síntese. A síntese pode exigir
uma primeira interação do usuário na página — clique uma vez na interface.

**O microfone não capta.**
Chrome, Edge ou Safari; permissão concedida; microfone não usado por outro aplicativo. O Firefox
não implementa a Web Speech API — use texto.

**Bloqueado após errar a senha.**
O bloqueio é temporário (5 minutos por padrão). Aguarde ou reduza `security.lockoutMs` na aba
*Política* — mas você precisa estar autenticado, então o caminho prático é esperar.

**Esqueci a senha do administrador.**
Como não há armazenamento em claro, a recuperação é por redefinição: limpe apenas a chave do
usuário no `localStorage` (`Ctrl+Shift+A` → *Sistema* → **LIMPAR DADOS DO NAVEGADOR** apaga
tudo, inclusive conversa) ou edite `config.js → security.seedUsers` para regravar o hash de
origem e recarregue. O `seedUsers` é escrito **apenas na primeira execução**, quando ainda não
existe base local.

**Automações não disparam.**
O agendador roda dentro da página: mantenha a aba aberta. A próxima execução de cada rotina
aparece na aba *Automações*.

**WhatsApp não envia.**
Sem confirmação ligada, mensagens ficam pendentes até você aprovar (`confirmar envio`). Verifique
também a lista branca de números e se as credenciais do backend escolhido foram gravadas no cofre.

---

## Privacidade e dados

Tudo o que a interface guarda fica **no navegador**: conversa, preferências, usuários (hash),
cofre cifrado, memória, rotinas e estado dos plugins. Nada é enviado a terceiros além das
chamadas que **você** configurar (provedor de modelo, clima, pesquisa) e do clima, que usa a
Open-Meteo sem chave. **LIMPAR DADOS DO NAVEGADOR**, na aba *Sistema*, apaga tudo isso.

Os valores de CPU, memória e rede são **estimados** a partir de sinais realmente disponíveis ao
navegador (carga da IA, FPS medido, latência HTTP, hardware, bateria). O navegador não expõe
métricas do sistema por segurança — o painel sinaliza isso como `ESTIMADO`.

---

## v2.1 — Modernização: mobile, voz, anexos, segurança e PWA

### 20 melhorias fora da caixa (v2.1)

1. **Navegação inferior mobile** — barra fixa com Fala, Central, Microfone (destaque), Painel ADM e Tela cheia
2. **Layout mobile-first** — breakpoints 1024/760/480 px, colunas laterais recolhidas, console de comando fixo
3. **Safe areas** — respeito a notch e gestos (`env(safe-area-inset-*)`)
4. **Gatilho "Olá, Jarvis"** — saudação falada com parte do dia ("Bom dia", "Boa tarde"…)
5. **Gatilho "Adeus, Jarvis"** — despedida falada e canal de voz encerrado automaticamente
6. **Troca de voz em 1 toque** — chip de perfil na barra de comando (Núcleo, Tático, Calmo, Bilíngue…)
7. **Botão de anexar** — foto, vídeo, áudio e documentos direto na barra do chat
8. **Arrastar e soltar** — solte arquivos sobre o chat para anexar
9. **Pré-visualização no chat** — imagens e vídeos renderizados; documentos em cartão
10. **Validação de anexos** — limite de 8 MB e tipos permitidos, com recusa explicada
11. **Copiar com toque longo** — qualquer mensagem copiável no celular
12. **Feedback sonoro** — sons discretos WebAudio para envio, anexo, confirmação e erro
13. **Indicador de bateria** — percentual na navegação, alerta em nível crítico
14. **Detector de conexão** — banner "modo local" quando a internet cai
15. **Tela cheia** — botão nativo na navegação mobile
16. **CAPTCHA no login** — desafio visual gerado por canvas antes de autenticar
17. **Vínculo de dispositivo** — aparelho reconhecido por impressão digital; dispositivo novo reforça o segundo fator
18. **Sessão com trava por inatividade** — logout automático após 10 min sem uso
19. **Console silenciado (stealth)** — erros e logs internos capturados sem vazar no DevTools do PC
20. **PWA de verdade** — instala como app (standalone), ícone próprio e funcionamento offline via service worker

### Segurança reforçada ("tampa todos os buracos")

- CAPTCHA obrigatório na autenticação, regenerado a cada tentativa
- Bloqueio temporário por tentativas (já existente) + atraso de comparação anti-timing
- Segundo fator TOTP/biometria forçado em dispositivo desconhecido
- Fila de admissão do servidor: aprovar, negar, cancelar e liberar entradas (painel ADM → aba Servidor)
- Verificação por SMS/e-mail (OTP no celular) pronta para ativar junto com o servidor

### Área do servidor (Termux)

Painel ADM → **Servidor**: configure o endpoint (ex.: `http://192.168.0.10:8080`), teste a conexão
(`/health`, latência em ms) e use os comandos reservados — ligar, desligar, reiniciar, fila de
admissão e verificação por SMS/e-mail. Todos ficam em espera até o servidor responder.

---

## 🧰 Open Tools Arsenal (novo)

30 ferramentas open source integradas ao JARVIS X (menu lateral → *Open Tools*), todas no navegador, sem chave de API:

1. **🧠 Conhecimento** — Wikipédia, Tradutor (MyMemory), Dicionário EN, Busca de Livros (Open Library), Hacker News
2. **🌍 Mundo** — Clima (Open-Meteo), Países (REST Countries), ISS ao vivo, Meu IP, Rastrear IP, Próximos Feriados (Nager.Date)
3. **💰 Mercado** — Câmbio (Frankfurter), Cripto (CoinGecko)
4. **🎨 Diversão** — Pokédex, Doguinhos, Gatinhos, Piada, Conselho, Paleta de Cores, Lorem Ipsum
5. **🛠 Dev** — GitHub Scan, QR Code, Senha Forte, UUID, Base64, SHA-256, JSON Format, Regex Tester
6. **⏱ Produtividade** — Contador de Texto, Pomodoro

## 🖥 Backend (FastAPI)

```bash
pip install -r requirements.txt
python -m uvicorn server.app:app --port 8080
```

O endpoint `/api/chat` chama o modelo local (Ollama em `JARVIS_MODEL_URL`, padrão `llama3.2`) e cai em modo degradado se o modelo estiver offline.

## ✅ CI e testes

```bash
python -m py_compile server/*.py
pytest -q
```

O GitHub Actions (`.github/workflows/ci.yml`) roda esses dois passos a cada push.
