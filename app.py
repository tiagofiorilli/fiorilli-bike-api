from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv
import requests

load_dotenv()
app = Flask(__name__)
CORS(app)

# Caminho dos tokens
TOKENS_PATH = os.getenv("TOKENS_PATH", "tokens.json")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SELLER_ID = os.getenv("SELLER_ID")

# === Funções auxiliares ===
def carregar_tokens():
    with open(TOKENS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def renovar_token():
    tokens = carregar_tokens()
    refresh_token = tokens["refresh_token"]

    url = "https://api.mercadolibre.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(url, data=data, headers=headers)
    r.raise_for_status()

    new_tokens = r.json()
    with open(TOKENS_PATH, "w", encoding="utf-8") as f:
        json.dump(new_tokens, f, indent=2, ensure_ascii=False)

    return new_tokens["access_token"]

def get_access_token():
    tokens = carregar_tokens()
    return tokens.get("access_token")

# === Rotas Flask ===
@app.route("/produtos", methods=["GET"])
def listar_produtos():
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.mercadolibre.com/users/{SELLER_ID}/items/search?limit=40"
    r = requests.get(url, headers=headers)

    if r.status_code == 401:
        token = renovar_token()
        headers["Authorization"] = f"Bearer {token}"
        r = requests.get(url, headers=headers)

    r.raise_for_status()
    dados = r.json()
    produtos = []

    for item_id in dados.get("results", []):
        info = requests.get(f"https://api.mercadolibre.com/items/{item_id}", headers=headers).json()
        produtos.append({
            "id": info.get("id"),
            "nome": info.get("title"),
            "preco": info.get("price"),
            "estoque": info.get("available_quantity"),
            "categoria": info.get("category_id"),
            "link": info.get("permalink")
        })

    return jsonify(produtos), 200

@app.route("/produto/<id>", methods=["GET"])
def obter_produto(id):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.mercadolibre.com/items/{id}"
    r = requests.get(url, headers=headers)

    if r.status_code == 401:
        token = renovar_token()
        headers["Authorization"] = f"Bearer {token}"
        r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return jsonify({"erro": "Produto não encontrado"}), 404

    info = r.json()
    return jsonify({
        "id": info.get("id"),
        "nome": info.get("title"),
        "preco": info.get("price"),
        "estoque": info.get("available_quantity"),
        "descricao": info.get("plain_text"),
        "link": info.get("permalink")
    })

@app.route("/buscar", methods=["GET"])
def buscar_produto():
    termo = request.args.get("q", "").lower()
    if not termo:
        return jsonify({"erro": "Parâmetro 'q' é obrigatório"}), 400

    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={termo}&seller_id={SELLER_ID}"
    r = requests.get(url, headers=headers)

    if r.status_code == 401:
        token = renovar_token()
        headers["Authorization"] = f"Bearer {token}"
        r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return jsonify({"erro": "Falha ao buscar produtos"}), 500

    data = r.json()
    resultados = [{
        "id": item.get("id"),
        "nome": item.get("title"),
        "preco": item.get("price"),
        "estoque": item.get("available_quantity"),
        "categoria": item.get("category_id"),
        "link": item.get("permalink")
    } for item in data.get("results", [])]

    return jsonify(resultados), 200

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "API Fiorilli Bike Shop ativa"}), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
