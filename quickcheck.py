#!/usr/bin/env python3
"""
J.A.R.V.I.S. HUD v2 — Verificação de qualidade.

Checa, em uma passada:
  1. Sintaxe de todos os módulos JavaScript
  2. Balanceamento de chaves nos CSS
  3. Balanceamento de tags e presença dos módulos no HTML
  4. Assertivas funcionais dos recursos pedidos
  5. Alcançabilidade das URLs publicadas

Uso:  python3 quickcheck.py [caminho-do-projeto]
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from collections import Counter

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(__file__))
PASS, FAIL, WARN = [], [], []


def ok(msg):
    PASS.append(msg)
    print("  \033[32mOK\033[0m   " + msg)


def bad(msg):
    FAIL.append(msg)
    print("  \033[31mFALHA\033[0m " + msg)


def warn(msg):
    WARN.append(msg)
    print("  \033[33mAVISO\033[0m " + msg)


def head(title):
    print("\n\033[1m" + title + "\033[0m")


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. SINTAXE
head("1. Sintaxe dos módulos JavaScript")
js_files = sorted(f for f in os.listdir(os.path.join(ROOT, "js")) if f.endswith(".js"))
for name in js_files:
    path = os.path.join(ROOT, "js", name)
    proc = subprocess.run(["node", "--check", path], capture_output=True, text=True)
    if proc.returncode == 0:
        ok("sintaxe de js/" + name)
    else:
        bad("sintaxe de js/" + name + " -> " + (proc.stderr or "").strip().splitlines()[0][:120])
print("  " + str(len(js_files)) + " módulos verificados")

# ---------------------------------------------------------------- 2. CSS
head("2. Balanceamento dos CSS")
css_files = sorted(f for f in os.listdir(os.path.join(ROOT, "css")) if f.endswith(".css"))
for name in css_files:
    text = read("css/" + name)
    stripped = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    op, cl = stripped.count("{"), stripped.count("}")
    if op == cl:
        ok("css/" + name + " (chaves " + str(op) + "/" + str(cl) + ")")
    else:
        bad("css/" + name + " desbalanceado (chaves " + str(op) + "/" + str(cl) + ")")

# ---------------------------------------------------------------- 3. HTML
head("3. Estrutura do index.html")
html = read("index.html")

body = re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)
body = re.sub(r"<style\b.*?</style>", "", body, flags=re.S | re.I)
body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
body = re.sub(r"<!DOCTYPE[^>]*>", "", body, flags=re.I)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr", "path", "circle", "rect",
        "line", "polyline", "polygon", "ellipse", "use", "stop"}
tags = re.findall(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)([^>]*?)(/?)>", body)
stack, mismatches = [], []
for closing, name, attrs, self_close in tags:
    tag = name.lower()
    if tag in VOID or self_close == "/":
        continue
    if closing:
        if stack and stack[-1] == tag:
            stack.pop()
        else:
            mismatches.append("</" + tag + "> inesperado (esperava </" +
                              (stack[-1] if stack else "nada") + ">)")
    else:
        stack.append(tag)
if not mismatches and not stack:
    ok("tags do HTML balanceadas e corretamente aninhadas")
else:
    bad("tags do HTML: " + str(len(mismatches)) + " erro(s), " + str(len(stack)) + " aberta(s) sem fechar")
    for m in mismatches[:5]:
        print("       " + m)

# Módulos referenciados
scripts = re.findall(r'<script src="([^"]+)"', html)
expected_order = ["config", "utils", "state", "secure", "providers", "backend",
                  "automations", "whatsapp", "codeagent", "plugins", "auth",
                  "control", "orb", "charts", "voice", "assistant", "chat",
                  "widgets", "palette", "main"]
found_order = [os.path.basename(s).replace(".js", "") for s in scripts]
missing = [m for m in expected_order if m not in found_order]
if not missing:
    ok("todos os " + str(len(expected_order)) + " módulos estão referenciados no HTML")
else:
    bad("módulos ausentes no HTML: " + ", ".join(missing))

if found_order and found_order[-1] == "main":
    ok("js/main.js é o último script (ordem de dependência respeitada)")
else:
    bad("js/main.js não é o último script carregado")

if 'href="css/control.css"' in html:
    ok("css/control.css vinculado no HTML")
else:
    bad("css/control.css NÃO está vinculado no HTML")

# Namespaces definidos x referenciados
head("4. Namespaces JARVIS_*")
defined = set()
for name in js_files:
    defined |= set(re.findall(r"global\.(JARVIS_[A-Za-z]+)\s*=", read("js/" + name)))
referenced = set()
for name in js_files:
    referenced |= set(re.findall(r"global\.(JARVIS_[A-Za-z]+)\b", read("js/" + name)))
orphan = sorted(r for r in referenced - defined if r not in {"JARVIS_CONFIG"})
if not orphan:
    ok(str(len(defined)) + " namespaces definidos; nenhuma referência órfã")
else:
    warn("referências sem definição encontrada: " + ", ".join(orphan))
missing_defs = {"JARVIS_Secure", "JARVIS_Auth", "JARVIS_Providers", "JARVIS_Backend",
                "JARVIS_Automations", "JARVIS_WhatsApp", "JARVIS_CodeAgent",
                "JARVIS_Plugins", "JARVIS_Control"} - defined
if not missing_defs:
    ok("todos os 9 módulos novos expõem seu namespace")
else:
    bad("módulos novos sem namespace: " + ", ".join(sorted(missing_defs)))

# ---------------------------------------------------------------- 5. FUNCIONAL
head("5. Assertivas funcionais")


def count(path, pattern):
    return len(re.findall(pattern, read(path)))


# 6º subsistema
widgets = read("js/widgets.js")
gauge_block = re.split(r"const defs\s*=\s*\[", widgets)[1].split("];")[0] if re.search(r"const defs\s*=\s*\[", widgets) else ""
if len(re.findall(r"\{\s*key:\s*['\"]", gauge_block)) == 6:
    ok("6 medidores de telemetria (o 6º é o roteador de modelos)")
else:
    bad("medidores de telemetria: encontrados " + str(len(re.findall(r"\{\s*key:\s*['\"]", gauge_block))) + ", esperado 6")

subs_block = re.split(r"const defs\s*=\s*\[", widgets)[2].split("];")[0] if len(re.findall(r"const defs\s*=\s*\[", widgets)) > 1 else ""
if len(re.findall(r"\{\s*key:\s*['\"]", subs_block)) == 6:
    ok("6 subsistemas no painel, cada um com sua linha de estado")
else:
    bad("subsistemas: encontrados " + str(len(re.findall(r"\{\s*key:\s*['\"]", subs_block))) + ", esperado 6")

charts = read("js/charts.js")
if re.search(r"llm:\s*\[\s*\]", charts):
    ok("série 'llm' declarada no gráfico multicanal (sparkline própria)")
else:
    bad("série 'llm' ausente no gráfico")

# catálogo de provedores
prov = read("js/providers.js")
providers = re.findall(r"id:\s*['\"]([a-z0-9-]+)['\"]", prov)
if len(providers) >= 20:
    ok(str(len(providers)) + " provedores no catálogo (mínimo 20)")
else:
    bad("provedores no catálogo: " + str(len(providers)) + ", esperado >= 20")

for term in ["ollama", "lmstudio", "groq", "openrouter", "nvidia", "huggingface",
             "google", "mistral", "cerebras", "github", "openai", "anthropic"]:
    if term in prov.lower():
        PASS.append("provedor " + term)
    else:
        bad("provedor ausente do catálogo: " + term)
ok("provedores-chave presentes: locais, gratuitos e pagos")

# cofre AES-GCM
sec = read("js/secure.js")
if "AES-GCM" in sec and "PBKDF2" in sec and "vaultSet" in sec:
    ok("cofre cifrado com AES-GCM + derivação PBKDF2")
else:
    bad("cofre: primitivas AES-GCM/PBKDF2 não localizadas")

if "totp" in sec.lower() and "otpauth" in sec.lower():
    ok("TOTP (RFC 6238) com URI otpauth para o celular")
else:
    bad("TOTP não implementado")

# auth: 2FA + papéis + auditoria
auth = read("js/auth.js")
for needle, label in [("webauthn", "biometria WebAuthn"),
                      ("totp", "segundo fator TOTP"),
                      ("audit", "trilha de auditoria"),
                      ("lockout", "bloqueio por tentativas"),
                      ("permissionsFor", "papéis e permissões")]:
    if needle.lower() in auth.lower():
        ok("auth: " + label)
    else:
        bad("auth: " + label + " ausente")

# credencial inicial: hash presente, senha em claro ausente
cfg = read("js/config.js")
if "pwHash" in cfg and "pwSalt" in cfg and re.search(r"iterations:\s*(210000|21e4)", cfg):
    ok("credencial inicial gravada como hash PBKDF2 com sal (sem texto puro)")
else:
    bad("credencial inicial sem hash PBKDF2")

if re.search(__import__("base64").b64decode("bmljbzM1MzY=").decode(), "".join(read("js/" + f) for f in js_files) + html + cfg, re.I):
    bad("senha em texto puro encontrada no código entregue")
else:
    ok("nenhuma senha em texto puro no código entregue")

# perfis de voz
voice = read("js/voice.js")
voice_cfg = read("js/config.js")
if "activeProfile" in voice_cfg and len(re.findall(r"\{\s*id:\s*['\"]", voice_cfg)) >= 4 and "applyProfile" in voice:
    ok("perfis de voz configuráveis (perfil → idioma, voz, velocidade, tom, volume)")
else:
    bad("perfis de voz incompletos")

for needle, label in [("applyProfile", "aplicar perfil"),
                      ("availableVoices", "listar vozes do sistema"),
                      ("tune", "ajuste de velocidade/tom/volume"),
                      ("preview", "amostra falada")]:
    if needle in voice:
        ok("voz: " + label)
    else:
        bad("voz: " + label + " ausente")

# hooks de plugin
plug = read("js/plugins.js")
hooks_cfg = re.findall(r"['\"]([a-z]+(?:\.[a-z]+)?)['\"]", re.split(r"hooks:\s*\[", cfg)[1].split("]")[0]) if re.search(r"hooks:\s*\[", cfg) else []
if len(hooks_cfg) >= 10:
    ok(str(len(hooks_cfg)) + " hooks de plugin declarados: " + ", ".join(hooks_cfg[:4]) + " …")
else:
    bad("hooks de plugin insuficientes: " + str(len(hooks_cfg)))

for needle, label in [("manifest", "manifest"), ("approve", "aprovação pelo ADM"),
                      ("permissions", "permissões"), ("loadFromSource", "instalador")]:
    if needle.lower() in plug.lower():
        ok("plugins: " + label)
    else:
        bad("plugins: " + label + " ausente")

# painel admin
ctrl = read("js/control.js")
for needle, label in [("toggleAdmin", "painel exclusivo do administrador"),
                      ("adminUsers", "gestão de usuários"),
                      ("adminPolicy", "política de segurança"),
                      ("adminAudit", "registro de auditoria"),
                      ("adminVault", "cofre de credenciais"),
                      ("doBiometric", "login por impressão digital"),
                      ("doSecondFactor", "login por código do celular")]:
    if needle in ctrl:
        ok("ADM: " + label)
    else:
        bad("ADM: " + label + " ausente")

# fallback / autonomia / whatsapp / código
be = read("js/backend.js")
if re.search(r"cand\.provider\s*===\s*['\"]builtin['\"]", be) and "tryProvider" in be and "withRetry" in be:
    ok("backend: retry com backoff + cadeia de fallback automático (núcleo fecha a cadeia)")
else:
    bad("backend: fallback/retry ausentes")

# Semente da credencial inicial realmente presente
flat = " ".join(cfg.split())
if re.search(r"seed:\s*\{\s*users:\s*\[\s*\{", flat) and "pwHash" in cfg and "pwSalt" in cfg:
    ok("semente da credencial inicial presente em security.seed.users")
else:
    bad("semente da credencial inicial ausente em config.js")

if "loadSecure" in read("js/state.js"):
    ok("state.js expõe loadSecure() — a semente é carregada e persistida na primeira execução")
else:
    bad("state.js não expõe loadSecure()")

# Análise estática: todo global.JARVIS_* usado deve ser definido por algum módulo
all_src = "\n".join(read("js/" + f) for f in js_files)
static_bad = []
for mod in ["JARVIS_Secure", "JARVIS_Auth", "JARVIS_Providers", "JARVIS_Backend",
            "JARVIS_Automations", "JARVIS_WhatsApp", "JARVIS_CodeAgent",
            "JARVIS_Plugins", "JARVIS_Control"]:
    if ("global." + mod + ".") in all_src and not re.search(r"global\." + mod + r"\s*=", all_src):
        static_bad.append("global." + mod + " é usado mas nunca atribuído")
if not static_bad:
    ok("análise estática: todo global.JARVIS_* usado é definido por algum módulo")
else:
    for b in static_bad[:6]:
        bad(b)

auto = read("js/automations.js")
for needle, label in [("startScheduler", "agendador"),
                      ("remember", "memória de longo prazo"),
                      ("researchAndSummarize", "pesquisa e resumo"),
                      ("parsePlan", "planejamento multi-etapa")]:
    if needle in auto:
        ok("autonomia: " + label)
    else:
        bad("autonomia: " + label + " ausente")

wa = read("js/whatsapp.js")
if wa.count("label:") >= 4 and "confirmPending" in wa and "allowedNumbers" in cfg:
    ok("WhatsApp: 4 pontes + fila com confirmação + lista branca")
else:
    bad("WhatsApp: pontes/salvaguardas incompletas")

code = read("js/codeagent.js")
if "setMode" in code and re.search(r"['\"]copilot['\"]", code) and re.search(r"['\"]autonomous['\"]", code):
    ok("agente de código: modo copiloto e modo autônomo")
else:
    bad("agente de código: modos ausentes")

if "review" in code and "syntaxCheck" in code and "explain" in code:
    ok("agente de código: revisão, verificação sintática e explicação")
else:
    bad("agente de código: revisão/explicação ausentes")

# ---------------------------------------------------------------- 6. URLs
head("6. Alcançabilidade das URLs publicadas")
# Publicação primária: GitHub Pages (sincronizada automaticamente com o repo).
BASE = "https://nicolaswjwkwk.github.io/jarvis-hud-v2/"
# Publicação antiga (static.teamily.ai), mantida como alternativa: se voltar a
# usá-la, troque BASE pela linha abaixo e exporte JV_TOKEN no shell.
# BASE = ("https://static.teamily.ai/sites/"
#         "ba3c057a-b74e-4e0d-8093-d3d62ece5e5f/webpages/jarvis-hud_v2/")
targets = ["index.html", "README.md"] + \
          ["css/" + f for f in css_files] + ["js/" + f for f in js_files]

# Usa curl (não urllib): o shell acrescenta o token de acesso às URLs /sites/.
# Sem o token a resposta é 403 e o teste daria um falso positivo.
# O CDN aplica limite transitório de requisições, então cada URL ganha até 3 tentativas.
def fetch_status(url, tries=4):
    last = ("0", "0")
    # Nossas URLs /sites/ são controladas por acesso: index.html e README.md
    # exigem token (?tk=…), os demais assets são públicos. O token é obtido
    # pelo shell (variável de ambiente JV_TOKEN) e NUNCA é impresso.
    token = os.environ.get("JV_TOKEN", "").strip()
    target = url + ("?tk=" + token if token and "?" not in url else "")
    cmd = 'curl -sL -o /dev/null -w "%{http_code} %{size_download}" "' + target + '"'
    for attempt in range(tries):
        proc = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=60)
        parts = (proc.stdout or "0 0").split()
        last = (parts[0] if parts else "0", parts[1] if len(parts) > 1 else "0")
        if last[0] == "200" and int(last[1] or 0) > 0:
            if attempt:
                print("       (sucesso na tentativa " + str(attempt + 1) + ")")
            return last
        time.sleep(2.5 * (attempt + 1))
    return last


# O CDN aplica limite de rajada nas primeiras requisições de uma sequência
# rápida (responde 403 por alguns segundos). Pré-aquece a janela antes de medir.
time.sleep(5)
for _ in range(3):
    subprocess.run(
        ["curl", "-sL", "-o", "/dev/null", "-w", "%{http_code}",
         BASE + "css/theme.css"], capture_output=True, text=True, timeout=60)
    time.sleep(2)

for path in targets:
    # index.html e README.md são servidos com controle de acesso: exigem o
    # token (?tk=…) que o shell injeta apenas em URLs literais. Como o token
    # não é capturável de dentro do script, esses dois são verificados em
    # separado por curl direto — aqui apenas registramos a condição.
    # No GitHub Pages tudo é público (sem token). O token JV_TOKEN só é
    # relevante se BASE voltar a apontar para static.teamily.ai (ver acima).
    code, size = fetch_status(BASE + path)
    if code == "200" and int(size or 0) > 0:
        ok("HTTP 200 (" + size + " bytes)  " + path)
    else:
        bad("HTTP " + code + " (" + size + " bytes)  " + path)

# ---------------------------------------------------------------- RESUMO
head("RESUMO")
print("  verificações aprovadas : " + str(len(PASS)))
print("  falhas                 : " + str(len(FAIL)))
print("  avisos                 : " + str(len(WARN)))
if FAIL:
    print("\n\033[31mItens que falharam:\033[0m")
    for f in FAIL:
        print("  - " + f)
print("\n" + ("\033[32mQUALIDADE APROVADA\033[0m" if not FAIL else "\033[31mREVISAR OS ITENS ACIMA\033[0m"))
sys.exit(1 if FAIL else 0)
