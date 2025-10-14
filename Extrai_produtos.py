import os
import json
import requests
from dotenv import load_dotenv

# === 🔧 Carregar variáveis de ambiente ===
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SELLER_ID = os.getenv("SELLER_ID")
TOKENS_PATH = os.getenv("TOKENS_PATH", "tokens.json")

# === 🧩 Carregar tokens ===
def carregar_tokens():
    if not os.path.exists(TOKENS_PATH):
        raise FileNotFoundError(f"Arquivo de tokens não encontrado: {TOKENS_PATH}")
    with open(TOKENS_PATH, "r", encoding="utf-8") as f:
        tokens = json.load(f)
    return tokens

tokens = carregar_tokens()
ACCESS_TOKEN = tokens.get("access_token")
REFRESH_TOKEN = tokens.get("refresh_token")

# === ♻️ Função para renovar token ===
def renovar_token():
    global ACCESS_TOKEN, REFRESH_TOKEN
    url = "https://api.mercadolibre.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    print("🔄 Renovando token de acesso...")
    r = requests.post(url, data=data, headers=headers)
    r.raise_for_status()
    new_tokens = r.json()

    with open(TOKENS_PATH, "w", encoding="utf-8") as f:
        json.dump(new_tokens, f, indent=2, ensure_ascii=False)

    ACCESS_TOKEN = new_tokens["access_token"]
    REFRESH_TOKEN = new_tokens["refresh_token"]
    print("✅ Token renovado com sucesso.")

# === 📦 Buscar produtos ===
def listar_produtos(limit=50, offset=0):
    url = f"https://api.mercadolibre.com/users/{SELLER_ID}/items/search?limit={limit}&offset={offset}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers)

    if r.status_code == 401:  # Token expirado
        renovar_token()
        headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"
        r = requests.get(url, headers=headers)

    r.raise_for_status()
    return r.json()

# === 🏷️ Buscar detalhes de cada produto ===
def detalhes_produto(item_id):
    url = f"https://api.mercadolibre.com/items/{item_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

# === 🚀 Executar ===
if __name__ == "__main__":
    dados = listar_produtos(limit=40)
    produtos = []

    for item_id in dados.get("results", []):
        info = detalhes_produto(item_id)
        produtos.append({
            "id": info.get("id"),
            "titulo": info.get("title"),
            "preco": info.get("price"),
            "estoque": info.get("available_quantity"),
            "condicao": info.get("condition"),
            "link": info.get("permalink")
        })

    # Salvar resultado
    OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "produtos.json")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(produtos, f, indent=2, ensure_ascii=False)

    print(f"✅ {len(produtos)} produtos salvos em {OUTPUT_PATH}")

