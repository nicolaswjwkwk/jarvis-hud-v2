(function(global){"use strict";const U=global.JARVIS_Utils,S=global.JARVIS_State,CFG=global.JARVIS_CONFIG,LANGUAGES=[{id:"javascript",label:"JavaScript",ext:"js",runnable:!0},{id:"typescript",label:"TypeScript",ext:"ts",runnable:!1},{id:"python",label:"Python",ext:"py",runnable:!1},{id:"html",label:"HTML",ext:"html",runnable:!1},{id:"css",label:"CSS",ext:"css",runnable:!1},{id:"sql",label:"SQL",ext:"sql",runnable:!1},{id:"bash",label:"Shell",ext:"sh",runnable:!1},{id:"json",label:"JSON",ext:"json",runnable:!1},{id:"yaml",label:"YAML",ext:"yml",runnable:!1},{id:"go",label:"Go",ext:"go",runnable:!1},{id:"rust",label:"Rust",ext:"rs",runnable:!1},{id:"java",label:"Java",ext:"java",runnable:!1}],REVIEW_RULES=[{id:"eval",severity:"critico",test:function(src){return/\beval\s*\(|new\s+Function\s*\(/.test(src)},title:"Uso de avaliação dinâmica",why:"eval/Function executam texto arbitrário e abrem brecha de injeção.",fix:"Substitua por um interpretador explícito, um mapa de ações ou JSON.parse."},{id:"innerhtml",severity:"alto",test:function(src){return/\.innerHTML\s*=/.test(src)&&!/escape|sanitize|DOMPurify/i.test(src)},title:"innerHTML sem sanitização",why:"Conteúdo vindo do usuário pode injetar HTML e scripts.",fix:"Use textContent, ou escape o valor antes; para listas, crie nós com createElement."},{id:"secrets",severity:"critico",test:function(src){return/(api[_-]?key|secret|password|token)\s*[:=]\s*['"][A-Za-z0-9_\-]{12,}['"]/i.test(src)},title:"Credencial embutida no código",why:"Chaves em texto puro vazam junto com o repositório.",fix:"Leia de variável de ambiente ou de um cofre cifrado."},{id:"loose-equality",severity:"baixo",test:function(src){return/[^=!<>]==[^=]/.test(src)},title:"Comparação frouxa (==)",why:"Coerção implícita de tipos causa bugs sutis.",fix:"Use === / !==."},{id:"var",severity:"baixo",test:function(src){return/(^|\s)var\s+/.test(src)},title:"Declaração var",why:"Escopo de função e hoisting imprevisível.",fix:"Troque por const (preferencialmente) ou let."},{id:"empty-catch",severity:"medio",test:function(src){return/catch\s*\([^)]*\)\s*\{\s*\}/.test(src)},title:"catch vazio",why:"O erro desaparece silenciosamente e fica impossível depurar.",fix:"Registre o erro e trate o estado; se não houver o que fazer, documente o porquê."},{id:"await-in-loop",severity:"medio",test:function(src){return/for\s*\([^)]*\)\s*\{[^}]*await\s/.test(src)},title:"await dentro de laço",why:"Executa em série e multiplica a latência total.",fix:"Colete as promessas e use Promise.all, ou processe em lotes."},{id:"todo",severity:"info",test:function(src){return/TODO|FIXME|XXX/.test(src)},title:"Pendência marcada no código",why:"Há trabalho reconhecidamente inacabado.",fix:"Abra uma tarefa e resolva antes de considerar o código pronto."},{id:"long-function",severity:"info",test:function(src){return src.split(`
`).length>220},title:"Trecho muito extenso",why:"Acima de ~200 linhas a leitura e o teste ficam caros.",fix:"Quebre em funções com responsabilidade única."},{id:"sql-concat",severity:"alto",test:function(src){return/(SELECT|INSERT|UPDATE|DELETE)[^;]*(\+\s*\w+|\$\{)/i.test(src)},title:"SQL montado por concatenação",why:"Vetor clássico de injeção de SQL.",fix:"Use consultas parametrizadas / prepared statements."},{id:"fetch-no-catch",severity:"medio",test:function(src){return/fetch\s*\(/.test(src)&&!/catch|\.then\s*\(\s*\w*[^,)]*,\s*/.test(src)&&!/try\s*\{/.test(src)},title:"fetch sem tratamento de erro",why:"Falha de rede derruba o fluxo sem mensagem ao operador.",fix:"Envolva em try/catch ou trate o segundo argumento de .then."},{id:"password-log",severity:"alto",test:function(src){return/console\.log\([^)]*(senha|password|token|secret)/i.test(src)},title:"Segredo enviado ao console",why:"O console fica no histórico e em capturas de tela.",fix:"Remova o log ou mascare o valor."}],CodeAgent={setMode(mode){const next=["off","copilot","autonomous"].indexOf(mode)!==-1?mode:"off";return S.patch("code",{mode:next}),CFG.autonomy.level=next==="autonomous"?"auto":next==="copilot"?"copilot":"manual",S.savePrefs(),S.emit("log",{level:"sys",msg:"agente de código: modo "+next}),S.emit("code.mode",next),S.emit("toast",{kind:next==="autonomous"?"warn":"ok",title:"Agente de código",body:next==="off"?"Desativado.":next==="copilot"?"Copiloto: sugere, revisa e explica — sem executar.":"Autônomo: planeja e executa multi-etapa com aprovação nas ações sensíveis."}),next},mode(){return S.data.code.mode},languages(){return LANGUAGES.slice()},languageLabel(id){const l=LANGUAGES.find(function(x){return x.id===id});return l?l.label:id},async generate(request,opts){const o=opts||{},ask=String(request||"").trim();if(!ask)return{ok:!1,error:"descreva o que o código deve fazer."};const lang=o.language||S.data.code.language||"javascript",label=this.languageLabel(lang);S.patch("code",{running:!0,language:lang,task:ask}),S.emit("log",{level:"sys",msg:"gerando código "+label+': "'+ask.slice(0,50)+'"'});const hasModel=!!(S.data.models.active&&S.data.models.active.provider)&&S.data.backend.mode!=="local";let code="",provider="esqueleto local";if(hasModel){const prompt="Escreva código em "+label+` para a solicitação abaixo. Responda SOMENTE com o bloco de código, sem comentários sobre ele fora do bloco, com identificadores claros e tratamento de erro onde fizer sentido.

SOLICITAÇÃO: `+ask,r=await global.JARVIS_Backend.ask(prompt,{maxTokens:o.maxTokens||1800});r.reply&&(code=this.extractCode(r.reply,lang),provider=r.providerLabel||r.provider)}code||(code=this.scaffold(ask,lang));const check=this.syntaxCheck(code,lang),review=this.review(code,lang),artifact=this.makeArtifact(code,lang,ask);return S.patch("code",{running:!1,lastResult:{code,lang,check,review,provider,artifact}}),S.emit("code.generated",{lang,chars:code.length,provider}),o.toChat!==!1&&S.emit("chat.push",{role:"assistant",text:"**Código gerado — "+label+"** *(via "+provider+")*\n\n```"+lang+`
`+code+"\n```\n\n**Verificação sintática:** "+(check.ok?"aprovada":"reprovada — "+check.error)+`
**Revisão:** `+this.reviewLine(review)}),{ok:!0,code,language:lang,check,review,artifact,provider}},extractCode(text,lang){const raw=String(text||""),fence=raw.match(/```[\w+#-]*\n([\s\S]*?)```/);return fence?fence[1].replace(/\s+$/,""):raw.split(`
`).filter(function(l){return!/^(aqui está|segue|claro|com certeza|espero|note que|explicação)/i.test(l.trim())}).join(`
`).trim()},scaffold(request,lang){const l=this.languageLabel(lang),lines=String(request||"").split(`
`).map(function(x){return"//   "+x}).join(`
`);switch(lang){case"python":return`# Esqueleto gerado pelo núcleo local do J.A.R.V.I.S.
# Configure um modelo no painel para obter código completo.
#
`+lines.replace(/\/\//g,"#")+`

def executar(entrada):
    """Ponto de entrada da tarefa."""
    if not entrada:
        raise ValueError("entrada obrigatória")
    resultado = processar(entrada)
    return resultado


def processar(entrada):
    # TODO: implementar a regra de negócio
    return entrada


if __name__ == "__main__":
    print(executar("exemplo"))
`;case"sql":return`-- Esqueleto gerado pelo núcleo local do J.A.R.V.I.S.
-- Prefira consultas parametrizadas a concatenar valores.

SELECT
    t.id,
    t.criado_em
FROM tabela AS t
WHERE t.criado_em >= :inicio
ORDER BY t.criado_em DESC
LIMIT :limite;
`;case"html":return`<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Documento</title>
</head>
<body>
  <main id="app"></main>
  <script src="app.js"><\/script>
</body>
</html>
`;case"css":return`/* Esqueleto gerado pelo núcleo local do J.A.R.V.I.S. */

:root {
  --cor-primaria: #0a7d95;
  --espaco: 16px;
}

.componente {
  display: flex;
  gap: var(--espaco);
  padding: var(--espaco);
}
`;default:return`/* Esqueleto gerado pelo núcleo local do J.A.R.V.I.S.
   Configure um modelo no painel de Modelos para gerar
   a implementação completa desta solicitação.

`+lines+`
*/

export function executar(entrada) {
  if (!entrada) throw new Error("entrada obrigatória");
  return processar(entrada);
}

function processar(entrada) {
  // TODO: implementar a regra de negócio
  return entrada;
}
`}},syntaxCheck(code,lang){const src=String(code||"");if(!src.trim())return{ok:!1,error:"código vazio",kind:"na"};const id=lang||S.data.code.language;if(id==="javascript"||id==="typescript"){if(id==="typescript")return this.bracketCheck(src,"heuristica");try{return new Function('"use strict";'+src.replace(/^\s*(?:import|export)\s.*$/gm,"")),{ok:!0,error:null,kind:"motor"}}catch(e){return{ok:!1,error:e&&e.message||String(e),kind:"motor"}}}if(id==="json")try{return JSON.parse(src),{ok:!0,error:null,kind:"motor"}}catch(e){return{ok:!1,error:e&&e.message||String(e),kind:"motor"}}return this.bracketCheck(src,"heuristica")},bracketCheck(src,kind){const pairs={"(":")","[":"]","{":"}"},closers={")":"(","]":"[","}":"{"},stack=[];let i=0,line=1,inStr=null,inLine=!1,inBlock=!1;for(;i<src.length;){const c=src[i],next=src[i+1];if(c===`
`){line++,inLine=!1,i++;continue}if(inLine){i++;continue}if(inBlock){if(c==="*"&&next==="/"){inBlock=!1,i+=2;continue}i++;continue}if(inStr){if(c==="\\"){i+=2;continue}c===inStr&&(inStr=null),i++;continue}if(c==="/"&&next==="/"){inLine=!0,i+=2;continue}if(c==="/"&&next==="*"){inBlock=!0,i+=2;continue}if(c==='"'||c==="'"||c==="`"){inStr=c,i++;continue}if(pairs[c]){stack.push({c,line}),i++;continue}if(closers[c]){const top=stack.pop();if(!top||top.c!==closers[c])return{ok:!1,error:'delimitador "'+c+'" sem par na linha '+line,kind,line};i++;continue}i++}if(stack.length){const open=stack[stack.length-1];return{ok:!1,error:'delimitador "'+open.c+'" aberto e não fechado (linha '+open.line+")",kind}}return{ok:!0,error:null,kind}},review(code,lang){const src=String(code||""),findings=[];REVIEW_RULES.forEach(function(rule){let hit=!1;try{hit=rule.test(src)}catch(e){hit=!1}hit&&findings.push({id:rule.id,severity:rule.severity,title:rule.title,why:rule.why,fix:rule.fix})});const order={critico:0,alto:1,medio:2,baixo:3,info:4};findings.sort(function(a,b){return(order[a.severity]||9)-(order[b.severity]||9)});const score=Math.max(0,100-findings.reduce(function(a,f){return a+({critico:26,alto:16,medio:8,baixo:4,info:1}[f.severity]||0)},0));return{findings,score,lines:src.split(`
`).length,chars:src.length,lang:lang||S.data.code.language}},reviewLine(review){if(!review||!review.findings.length)return"nenhum apontamento — nota "+(review?review.score:100)+"/100.";const crit=review.findings.filter(function(f){return f.severity==="critico"||f.severity==="alto"}).length;return review.findings.length+" apontamento(s), "+crit+" de severidade alta · nota "+review.score+"/100."},reviewText(text){const code=this.extractCode(text,S.data.code.language),r=this.review(code,S.data.code.language);return S.patch("code",{lastResult:{code,review:r,lang:S.data.code.language}}),r},autoFix(code){let out=String(code||"");const applied=[];/(^|\s)var\s+/.test(out)&&(out=out.replace(/(^|\s)var\s+/g,"$1const "),applied.push("var → const")),/[^=!<>]==[^=]/.test(out)&&(out=out.replace(/([^=!<>])==([^=])/g,"$1===$2"),out=out.replace(/([^=!<>])!=([^=])/g,"$1!==$2"),applied.push("== / != → === / !==")),/catch\s*\(([^)]*)\)\s*\{\s*\}/.test(out)&&(out=out.replace(/catch\s*\(([^)]*)\)\s*\{\s*\}/g,'catch ($1) { console.error("[$1]", $1); }'),applied.push("catch vazio preenchido"));const check=this.syntaxCheck(out,S.data.code.language);return check.ok?(S.patch("code",{lastResult:{code:out,lang:S.data.code.language,check}}),S.emit("log",{level:"ok",msg:"correção automática aplicada: "+(applied.join(", ")||"nada a corrigir")}),{ok:!0,code:out,applied}):(S.emit("log",{level:"warn",msg:"correção automática revertida: quebraria a sintaxe"}),{ok:!1,code,applied:[],error:check.error})},explain(code,lang){const src=String(code||"").trim();if(!src)return{ok:!1,error:"nada a explicar"};const l=this.languageLabel(lang||S.data.code.language),lines=src.split(`
`),functions=(src.match(/(?:function\s+\w+|=>|\bdef\s+\w+|class\s+\w+)/g)||[]).length,branches=(src.match(/\b(if|else if|elif|switch|case|catch|except)\b/g)||[]).length,loops=(src.match(/\b(for|while|forEach|map|filter|reduce)\b/g)||[]).length,asyncOps=(src.match(/\b(await|async|then|Promise)\b/g)||[]).length;return{ok:!0,text:["**Leitura do trecho — "+l+"**","• Extensão: "+lines.length+" linha(s), "+src.length+" caracteres.","• Estruturas: "+functions+" definição(ões), "+branches+" desvio(s) condicional(is), "+loops+" laço(s)/iteração(ões).",asyncOps?"• Concorrência: "+asyncOps+" ponto(s) assíncrono(s) — o fluxo depende de promessas.":"• Concorrência: execução totalmente síncrona.","• Verificação sintática: "+(this.syntaxCheck(src,lang||S.data.code.language).ok?"passou":"falhou"),"• Revisão de segurança: "+this.reviewLine(this.review(src,lang||S.data.code.language))].join(`
`)}},async runTask(goal,opts){const o=opts||{},Auto=global.JARVIS_Automations;if(S.data.code.mode==="off")return{ok:!1,error:"Ative o agente (copiloto ou autônomo) para executar tarefas."};S.emit("log",{level:"sys",msg:'tarefa de código: "'+String(goal).slice(0,60)+'"'});const plan=await Auto.plan(goal);return plan.ok?S.data.code.mode==="copilot"&&CFG.autonomy.confirmDestructive&&!o.approved?(S.patch("code",{steps:plan.steps,task:goal,progress:0}),S.emit("code.plan.ready",plan),S.emit("chat.push",{role:"assistant",text:"**Plano proposto ("+plan.steps.length+" passos, "+plan.planner+`)**
`+plan.steps.map(function(s,i){return i+1+". "+s.label+"  `"+s.tool+"`"}).join(`
`)+`

Confirme para executar — ou aprove na central de controle.`}),{ok:!0,pending:!0,plan}):Auto.runPlan(plan,{mode:S.data.code.mode}):plan},async approvePlan(){const steps=S.data.code.steps||[];if(!steps.length)return{ok:!1,error:"nenhum plano aguardando aprovação."};const plan={goal:S.data.code.task,steps},Auto=global.JARVIS_Automations;return S.emit("log",{level:"sys",msg:"plano aprovado pelo operador"}),Auto.runPlan(plan,{mode:"autonomous"})},cancelPlan(){const had=!!(S.data.code.steps||[]).length;return S.patch("code",{steps:[],running:!1,task:null,progress:0}),had&&S.emit("log",{level:"warn",msg:"plano de código cancelado"}),had},makeArtifact(code,lang,title){const def=LANGUAGES.find(function(x){return x.id===lang})||{ext:"txt"};return{filename:(U.normalize(title||"trecho").split(" ").slice(0,5).join("-").replace(/[^a-z0-9-]/g,"")||"trecho")+"."+def.ext,language:lang,bytes:new Blob([String(code||"")]).size,lines:String(code||"").split(`
`).length,createdAt:Date.now()}},download(){const r=S.data.code.lastResult;if(!r||!r.code)return S.emit("toast",{kind:"warn",title:"Código",body:"Nada para exportar ainda."}),!1;const art=r.artifact||this.makeArtifact(r.code,r.lang,"trecho"),blob=new Blob([r.code],{type:"text/plain;charset=utf-8"}),url=URL.createObjectURL(blob),a=document.createElement("a");return a.href=url,a.download=art.filename,document.body.appendChild(a),a.click(),document.body.removeChild(a),setTimeout(function(){URL.revokeObjectURL(url)},1500),S.emit("log",{level:"ok",msg:"artefato exportado: "+art.filename}),!0},copy(){const r=S.data.code.lastResult;return!r||!r.code?!1:navigator.clipboard&&navigator.clipboard.writeText?(navigator.clipboard.writeText(r.code).catch(function(){}),S.emit("toast",{kind:"ok",title:"Código copiado",body:r.artifact?r.artifact.filename:""}),!0):!1},runSandboxed(){const r=S.data.code.lastResult;if(!r||!r.code)return{ok:!1,error:"nada para executar"};if(r.lang!=="javascript")return{ok:!1,error:"Execução isolada disponível apenas para JavaScript. Use o interpretador da sua máquina para "+this.languageLabel(r.lang)+"."};const check=this.syntaxCheck(r.code,"javascript");if(!check.ok)return{ok:!1,error:"sintaxe inválida: "+check.error};const out=[],frame=document.createElement("iframe");frame.setAttribute("sandbox","allow-scripts"),frame.style.cssText="position:fixed;width:1px;height:1px;opacity:0;pointer-events:none;",document.body.appendChild(frame);const doc=frame.contentDocument,script=doc.createElement("script");return script.textContent='var __log=function(){try{parent.postMessage({__jarvis:1,args:Array.prototype.slice.call(arguments).map(String)},"*")}catch(e){}};console.log=__log;console.error=__log;console.warn=__log;try{'+r.code+'}catch(e){__log("ERRO: "+(e&&e.message||e));}',doc.body.appendChild(script),new Promise(function(resolve){const handler=function(ev){!ev.data||!ev.data.__jarvis||out.push(ev.data.args.join(" "))};global.addEventListener("message",handler),setTimeout(function(){global.removeEventListener("message",handler),frame.parentNode&&frame.parentNode.removeChild(frame),S.emit("code.output",out),S.emit("toast",{kind:out.length?"ok":"warn",title:"Execução isolada",body:out.length?"Saída: "+out.slice(0,2).join(" | ").slice(0,140):"Sem saída no console."}),resolve({ok:!0,output:out})},900)})},describe(){const c=S.data.code,labels={off:"DESLIGADO",copilot:"COPILOTO",autonomous:"AUTÔNOMO"};return{mode:c.mode,label:labels[c.mode]||c.mode,running:c.running,task:c.task,progress:c.progress,steps:(c.steps||[]).length,done:(c.steps||[]).filter(function(s){return s.status==="done"}).length,language:this.languageLabel(c.language),lastScore:c.lastResult&&c.lastResult.review?c.lastResult.review.score:null,history:c.history.length}}};global.JARVIS_CodeAgent=CodeAgent})(window);
