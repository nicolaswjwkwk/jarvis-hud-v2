# Integrações Google no site

O HUD tem três integrações Google configuráveis direto no painel de
Configurações, sem alterar código. Tudo fica salvo no navegador
(localStorage) — nenhum segredo vai para o repositório.

## 1. Login Google direto (GIS) — funciona sem backend

1. Acesse https://console.cloud.google.com/apis/credentials
2. Crie um "OAuth client ID" do tipo *Web application*
3. Em *Authorized JavaScript origins*, adicione:
   https://nicolaswjwkwk.github.io
4. Copie o ID (termina em .apps.googleusercontent.com)
5. Cole no campo **Login Google direto (GIS)** nas Configurações do site

Com isso o botão "Entrar com Google" valida o token direto com o Google
(endpoint público tokeninfo) e cria a sessão local. Se um backend estiver
configurado, o fluxo OAuth completo do servidor continua tendo prioridade
(essa via exige GOOGLE_CLIENT_ID/SECRET no .env do backend, ver docs/AUTH.md).

## 2. Google Analytics 4

1. Acesse https://analytics.google.com e crie uma propriedade Web
2. Origem informada: https://nicolaswjwkwk.github.io
3. Copie o ID de medição (formato G-XXXXXXXXXX)
4. Cole no campo **Google Analytics 4** nas Configurações

O gtag.js é injetado automaticamente e já envia page_view.

## 3. Google Ads

1. No Google Ads, aba Ferramentas > Conversões > Nova conversão > Site
2. Copie o ID de conversão (formato AW-XXXXXXXXX)
3. Cole no campo **Google Ads** nas Configurações

Com o GA4 e o Ads ligados na mesma conta Google, o Analytics passa a
enriquecer os relatórios de conversão automaticamente.

## Ordem de prioridade do login

1. Backend configurado com OAuth completo → fluxo do servidor
2. ID GIS configurado → login direto pelo navegador
3. Nenhum dos dois → aviso para configurar
