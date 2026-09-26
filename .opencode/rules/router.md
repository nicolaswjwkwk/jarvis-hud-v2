# Router — regras de roteamento e custo

Mapa de roteamento:
- Tarefa de código → modelo de código (Qwen2.5-Coder, DeepSeek-Coder, StarCoder2, Code Llama)
- Tarefa de raciocínio → modelo de raciocínio (DeepSeek-R1, Nemotron Ultra, Qwen3)
- Tarefa de pesquisa → navegador/webfetch + fontes primárias, comparar e citar origem
- Tarefa de imagem → modelo de imagem; nunca inventar informação visual
- Tarefa de automação → workflow/agendamento existente; não duplicar o que já roda
- Tarefa de banco → ferramenta de dados adequada ao volume e privacidade
- Documento longo → recuperar só trechos relevantes (RAG)
- Tarefa complexa/multiárea → orquestrar subagentes, cada um com o mínimo de contexto

Controle de custo: sempre confirme plano e limites de uma API antes de usar; não
consuma créditos pagos sem autorização explícita quando houver risco de cobrança.

Verificação antes de finalizar: testes quando possível, sintaxe, erros, nenhuma
etapa essencial esquecida. Segredos só em variáveis de ambiente.
