# Modelo local e catálogo de modelos gratuitos

O catálogo de modelos gratuitos fica em [`models/free-models.json`](../models/free-models.json).
Ele é carregado pelo módulo `js/free-models.js` e foi separado da lógica da interface para que
modelos novos possam ser adicionados sem expor chaves nem alterar o HUD.

## OpenRouter

A configuração de um provedor OpenRouter exige uma chave criada pelo usuário. O JARVIS não
embute chaves, não coleta credenciais e não promete disponibilidade permanente: limites, nomes,
políticas e disponibilidade podem mudar. A interface deve testar o modelo antes de usá-lo.

Modelos listados incluem Nemotron 3.5 Lightning, Nemotron 3 Ultra, Ling 3.0 Flash, Space Bunny,
Llama, Mistral, DeepSeek, Qwen e Gemini quando publicados como opções gratuitas. MiMo-V2.6-Flash,
Muse Spark 1.3 e OpenCode Zen permanecem na lista de pendências porque não há um identificador
público estável verificado para eles; não foram inventados aliases que poderiam quebrar chamadas.

## Outros modelos open source gratuitos

Para uso local e privado, prefira Ollama, LM Studio ou llama.cpp. Esses runtimes não exigem uma
chave de API e podem funcionar sem internet depois que os pesos forem baixados. O endpoint local
do projeto continua sendo `http://localhost:8080` e encaminha as mensagens para o endpoint
OpenAI-compatible configurado por `JARVIS_MODEL_URL`.

Sempre confira a licença do modelo e os termos do provedor antes de redistribuir pesos, usar em
produção ou oferecer um serviço pago.

## Novidades v3.1

- Novos provedores no catálogo (js/providers.js): Meta Llama API, SiliconFlow,
  Cloudflare Workers AI e Fish Audio (voz).
- OpenCode completo na raiz: opencode.json com 17 provedores e dezenas de
  modelos, agentes, comandos, plugin de proteção e regras em .opencode/.
- Motor de voz Fish Audio com fallback automático para a voz do navegador.
- Camada css/refined.css: interface mais limpa e sofisticada.
- Documentação completa em docs/OPENCODE.md.

