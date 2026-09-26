(function(global){"use strict";const U=global.JARVIS_Utils,S=global.JARVIS_State,CFG=global.JARVIS_CONFIG,Chat={root:null,chips:null,countEl:null,messages:[],suggestions:[],init(refs){return this.root=refs.root,this.chips=refs.chips,this.countEl=refs.count,S.data.chat.history=this.messages,this.restore(),this.renderSuggestions(),S.on("chat.push",payload=>this.push(payload)),S.on("chat.clear",()=>this.clear()),S.on("chat.typing",on=>this.typing(on)),this},restore(){const saved=U.storeGet(CFG.history.storageKey,null);if(saved&&Array.isArray(saved.messages)&&saved.messages.length){this.messages=saved.messages.slice(-CFG.history.maxMessages),S.data.chat.history=this.messages,this.messages.forEach(m=>this.render(m,!0)),this.scroll(!0),this.updateCount(),S.emit("log",{level:"sys",msg:"histórico restaurado ("+this.messages.length+" mensagens)"});return}this.greet()},persist:(function(){let timer=null;return function(){clearTimeout(timer),timer=setTimeout(()=>{U.storeSet(CFG.history.storageKey,{messages:this.messages.slice(-CFG.history.maxMessages),savedAt:Date.now()})},420)}})(),greet(){const h=new Date().getHours(),period=h<12?"Bom dia":h<18?"Boa tarde":"Boa noite";this.push({role:"system",text:period+", operador. **"+CFG.assistant.name+"** iniciado e "+(S.data.voice.supported?"com o canal de voz disponível":"operando em modo texto")+". Digite **ajuda** para o catálogo de intenções, use **Ctrl+K** para a paleta de comandos ou toque no microfone para falar."})},push(payload){const msg={id:U.id(),role:payload.role||"assistant",text:payload.text||"",at:payload.at||Date.now(),stream:!!payload.stream,meta:payload.meta||null};this.messages.push(msg),this.messages.length>CFG.history.maxMessages&&this.messages.shift(),S.data.chat.history=this.messages;const node=this.render(msg);return this.scroll(),this.updateCount(),this.persist(),msg.stream&&setTimeout(()=>this.typeOut(msg.id,msg.text),150+Math.random()*170),node},render(msg,silent){const wrap=U.el("article","msg msg--"+msg.role);wrap.setAttribute("data-id",msg.id);const initial=msg.role==="user"?"OP":msg.role==="system"?"··":msg.role==="error"?"!!":"JR",avatar=U.el("div","msg__avatar",initial),body=U.el("div","msg__body"),name=msg.role==="user"?CFG.assistant.operator:msg.role==="system"?"SISTEMA":msg.role==="error"?"FALHA":CFG.assistant.name,meta=U.el("div","msg__meta");meta.innerHTML="<b>"+U.escape(name)+"</b><span>"+U.stamp(new Date(msg.at))+"</span>"+(msg.meta?"<span>"+U.escape(msg.meta)+"</span>":"");const text=U.el("div","msg__text");msg.stream?text.innerHTML='<span class="typing"><i></i><i></i><i></i></span>':text.innerHTML=U.rich(msg.text).replace(/\n/g,"<br>");const actions=U.el("div","msg__actions");if(msg.role!=="user"&&msg.text){const copyBtn=U.el("button","","copiar");copyBtn.type="button",U.on(copyBtn,"click",()=>this.copy(msg.text,copyBtn));const speakBtn=U.el("button","","ouvir");speakBtn.type="button",U.on(speakBtn,"click",()=>{global.speechSynthesis&&(S.data.voice.muted=!1,global.JARVIS_Voice.speak(msg.text,{force:!0}))}),actions.appendChild(copyBtn),actions.appendChild(speakBtn)}return body.appendChild(meta),body.appendChild(text),body.appendChild(actions),wrap.appendChild(avatar),wrap.appendChild(body),this.root.appendChild(wrap),silent||S.emit("chat.rendered",msg),wrap},typeOut(id,fullText){const node=this.root.querySelector('[data-id="'+id+'"] .msg__text'),msg=this.messages.find(m=>m.id===id);if(!node){msg&&(msg.stream=!1);return}const rich=U.rich(fullText).replace(/\n/g,"<br>"),tokens=fullText.match(/\S+\s*/g)||[fullText];let i=0,buffer="";S.setCore("speaking");const tick=()=>{if(i>=tokens.length){node.innerHTML=rich,msg&&(msg.stream=!1),this.persist(),S.data.voice.speaking||S.setCore(S.data.voice.listening?"listening":"online");return}const step=1+(Math.random()<.35?1:0);buffer=tokens.slice(0,i+step).join(""),i+=step,node.innerHTML=U.rich(buffer).replace(/\n/g,"<br>")+'<span class="caret"></span>',this.scroll(),setTimeout(tick,18+Math.random()*26)};tick()},typing(on){const existing=this.root.querySelector(".msg--pending");if(on&&!existing){const wrap=U.el("article","msg msg--assistant msg--pending");wrap.innerHTML='<div class="msg__avatar">JR</div><div class="msg__body"><div class="msg__meta"><b>'+U.escape(CFG.assistant.name)+'</b><span>processando</span></div><div class="msg__text"><span class="typing"><i></i><i></i><i></i></span></div></div>',this.root.appendChild(wrap),this.scroll()}else!on&&existing&&existing.remove()},renderSuggestions(list){this.suggestions=list||global.JARVIS_Assistant.suggestions(),this.chips&&(this.chips.innerHTML="",this.suggestions.forEach(text=>{const chip=U.el("button","chip",U.escape(text));chip.type="button",U.on(chip,"click",()=>S.emit("command.submit",text)),this.chips.appendChild(chip)}))},scroll(instant){this.root&&(instant?(this.root.style.scrollBehavior="auto",this.root.scrollTop=this.root.scrollHeight,this.root.style.scrollBehavior=""):this.root.scrollTop=this.root.scrollHeight)},updateCount(){if(!this.countEl)return;const n=this.messages.length;this.countEl.textContent=n+" MSG"},copy(text,btn){const done=()=>{const original=btn.textContent;btn.textContent="copiado",setTimeout(()=>{btn.textContent=original},1400)};navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(text).then(done).catch(()=>this.fallbackCopy(text,done)):this.fallbackCopy(text,done)},fallbackCopy(text,done){const ta=document.createElement("textarea");ta.value=text,ta.style.position="fixed",ta.style.opacity="0",document.body.appendChild(ta),ta.select();try{document.execCommand("copy"),done()}catch(e){}document.body.removeChild(ta)},clear(){this.messages=[],S.data.chat.history=this.messages,S.data.chat.count=0,this.root.innerHTML="",U.storeDel(CFG.history.storageKey),this.updateCount(),S.emit("log",{level:"warn",msg:"histórico de conversa expurgado"}),this.push({role:"system",text:"Histórico expurgado. Canal limpo e pronto para novas instruções."})},export(){const lines=this.messages.map(m=>{const who=m.role==="user"?CFG.assistant.operator:m.role==="system"?"SISTEMA":CFG.assistant.name;return"["+U.stamp(new Date(m.at))+"] "+who+": "+m.text}),header=["# "+CFG.assistant.name+" — transcrição do canal","# exportado em "+new Date().toLocaleString("pt-BR"),"# mensagens: "+this.messages.length,""],blob=new Blob([header.concat(lines).join(`
`)],{type:"text/plain;charset=utf-8"}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url,a.download="jarvis-transcricao-"+U.todayISO()+".txt",document.body.appendChild(a),a.click(),document.body.removeChild(a),setTimeout(()=>URL.revokeObjectURL(url),1500),S.emit("log",{level:"ok",msg:"transcrição exportada ("+this.messages.length+" mensagens)"}),S.emit("toast",{kind:"ok",title:"Exportação concluída",body:"Transcrição salva como arquivo de texto."})}};global.JARVIS_Chat=Chat})(window);

/* ==== JARVIS_Files · anexos (foto/vídeo/arquivo) no chat (v2.1) ========== */
(function(global){"use strict";
var Files={max:8*1024*1024,preview:4*1024*1024,_ok:false,
fmt(b){if(b<1024)return b+" B";if(b<1048576)return(b/1024).toFixed(1)+" KB";return(b/1048576).toFixed(1)+" MB"},
kindOf(f){var t=(f.type||"").toLowerCase();
if(t.indexOf("image/")===0)return"image";
if(t.indexOf("video/")===0)return"video";
if(t.indexOf("audio/")===0)return"audio";
if(t==="application/pdf"||/\.(pdf|txt|md|json|zip|csv)$/i.test(f.name))return"doc";
return"other"},
validate(f){if(f.size>this.max)return"Arquivo acima de 8 MB: "+f.name;
var k=this.kindOf(f);return(k==="other")?"Tipo não suportado: "+f.name:null},
send(file){var self=this,U=global.JARVIS_Utils,S=global.JARVIS_State,C=global.JARVIS_Chat,FX=global.JARVIS_FX,doc=global.document;
var err=this.validate(file);
if(err){FX&&FX.play("err");S&&S.emit("toast",{kind:"err",title:"Anexo recusado",body:err});return;}
var k=this.kindOf(file);
var msg=C.push({role:"user",text:"Enviou "+file.name+" ("+this.fmt(file.size)+")",meta:"anexo"});
FX&&FX.play("attach");
S&&S.emit("log",{level:"sys",msg:"anexo recebido: "+file.name+" ("+this.fmt(file.size)+")"});
var node=doc.querySelector('[data-id="'+msg.id+'"] .msg__text');
if(!node)return;
if(file.size<=this.preview&&(k==="image"||k==="video")){
var rd=new FileReader();
rd.onload=function(){var el;
if(k==="image"){el=doc.createElement("img");el.className="hud-thumb";el.alt=file.name;el.src=rd.result;}
else{el=doc.createElement("video");el.className="hud-thumb";el.controls=true;el.preload="metadata";el.src=rd.result;}
node.appendChild(el);S&&C.scroll&&C.scroll();};
rd.readAsDataURL(file);}else{
var card=doc.createElement("div");card.className="hud-filecard";
card.innerHTML='<span class="hud-filecard__icon">'+(k==="doc"?"DOC":k.toUpperCase())+'</span><span class="hud-filecard__name">'+U.escape(file.name)+'</span>';
node.appendChild(card);}},
handleFiles(list){for(var i=0;i<list.length;i++)this.send(list[i]);},
init(){if(this._ok)return;this._ok=true;
var doc=global.document,S=global.JARVIS_State,FX=global.JARVIS_FX;
var root=doc.getElementById("panel-console");
if(root){var inp=doc.createElement("input");
inp.type="file";inp.multiple=true;inp.hidden=true;inp.className="hud-file-input";
inp.accept="image/*,video/*,audio/*,application/pdf,.txt,.md,.json,.zip,.csv";
var btn=doc.createElement("button");
btn.type="button";btn.className="hud-attach";
btn.title="Anexar foto, vídeo ou arquivo";btn.setAttribute("aria-label","Anexar arquivo");
btn.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>';
var mic=doc.getElementById("btn-mic");
mic?root.insertBefore(btn,mic):root.insertBefore(btn,root.firstChild);
root.appendChild(inp);
btn.addEventListener("click",function(){inp.click()});
inp.addEventListener("change",function(){if(inp.files&&inp.files.length)Files.handleFiles(inp.files);inp.value="";});
var chat=doc.getElementById("chat");
if(chat){["dragover","dragenter"].forEach(function(ev){chat.addEventListener(ev,function(e){e.preventDefault();chat.classList.add("hud-dropping")})});
["dragleave","drop"].forEach(function(ev){chat.addEventListener(ev,function(e){e.preventDefault();chat.classList.remove("hud-dropping");
if(ev==="drop"&&e.dataTransfer&&e.dataTransfer.files&&e.dataTransfer.files.length)Files.handleFiles(e.dataTransfer.files);})});}}
/* copiar mensagem com toque longo (mobile) */
var hist=doc.getElementById("chat");
if(hist){var timer=null,node=null;
hist.addEventListener("touchstart",function(e){var t=e.target.closest?e.target.closest(".msg"):null;if(!t)return;
node=t;timer=setTimeout(function(){var txt=node.querySelector(".msg__text");var txtEl=txt&&(txt.innerText||txt.textContent);
if(txtEl&&(doc.getSelection?doc.getSelection().toString()==="":true)){
try{if(navigator.clipboard)navigator.clipboard.writeText(txtEl);FX&&FX.play("ok");
S&&S.emit("toast",{kind:"ok",title:"Copiado",body:"Mensagem copiada para a área de transferência."});}catch(err){}}},550);},{passive:true});
["touchend","touchmove","touchcancel"].forEach(function(ev){hist.addEventListener(ev,function(){clearTimeout(timer)},{passive:true});});}
}};
global.JARVIS_Files=Files;
if(global.document){if(global.document.readyState!=="loading")Files.init();else global.document.addEventListener("DOMContentLoaded",function(){Files.init()});}
})(window);
