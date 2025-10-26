"""
Script oficial para gerar tokens de acesso do Mercado Livre usando o fluxo PKCE (Proof Key for Code Exchange)
Compatível com apps novos (2024/2025). Não requer CLIENT_SECRET.
Autor: Fiorilli Bike Shop / Tiago Fiorilli
"""

import base64
import hashlib
import os
import requests
import json

# ======================================================
# 🔧 CONFIGURAÇÕES DO SEU APLICATIVO NO MERCADO LIVRE
# ======================================================
CLIENT_ID = "2567516025524535"
CLIENT_SECRET = "QPRSwuNcIIYYBHr52mlMlSDGVFMqM6H2"
REDIRECT_URI = "https://www.fiorillibikes.com.br"   # deve ser exatamente igual ao cadastrado no app

# ======================================================
# ⚙️ GERAÇÃO DO CODE VERIFIER E CODE CHALLENGE (PKCE)
# ======================================================
def gerar_pkce():
    verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b'=').decode('utf-8')
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode('utf-8')).digest()
    ).rstrip(b'=').decode('utf-8')
    return verifier, challenge

verifier, challenge = gerar_pkce()

# ======================================================
# 🔗 ETAPA 1: GERA O LINK DE AUTORIZAÇÃO
# ======================================================
print("\n================= ETAPA 1 =================")
print("👉 Acesse o link abaixo para autorizar o aplicativo:")
print("=====================================================\n")
print(
    f"https://auth.mercadolibre.com/authorization?"
    f"response_type=code&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&code_challenge={challenge}"
    f"&code_challenge_method=S256"
)
print("\n=====================================================")
print("Após autorizar, copie o valor do parâmetro 'code=' da URL retornada.\n")

auth_code = input("Cole aqui o código (começa com TG-...): ").strip()

# ======================================================
# 🔄 ETAPA 2: TROCA O CÓDIGO PELO TOKEN DE ACESSO
# ======================================================
url = "https://api.mercadolibre.com/oauth/token"
data = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,  # ✅ MANTÉM AGORA
    "code": auth_code,
    "redirect_uri": REDIRECT_URI,
    "code_verifier": verifier
}

print("\n🔁 Solicitando token ao Mercado Livre...\n")
resp = requests.post(url, data=data)

print("📦 Resposta da API:")
print(resp.status_code, resp.text)

# ======================================================
# 💾 ETAPA 3: SALVA O TOKEN NO ARQUIVO JSON
# ======================================================
if resp.status_code == 200:
    tokens = resp.json()
    with open("tokens.json", "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    print("\n✅ tokens.json criado com sucesso!")
else:
    print("\n❌ Falha ao gerar token.")
    print("Verifique se:")
    print(" - O redirect_uri está idêntico ao cadastrado no painel do Mercado Livre")
    print(" - O código (code=TG-...) é o mesmo gerado após autorizar o app")
    print(" - Não fechou o terminal antes de colar o código (verifier precisa ser o mesmo)")
