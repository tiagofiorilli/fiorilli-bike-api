from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv
import requests

# === Configuração inicial ===
load_dotenv()
app = Flask(__name__)
CORS(app)

# === Variáveis de ambiente ===
TOKENS_PATH = os.getenv("TOKENS_PATH", "tokens.json")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SELLER_ID = os.getenv("SELLER_ID")

# ================================================================
# 🔧 FUNÇÕES AUXILIARES
# ================================================================

def carregar_tokens():
    return {
        "access_token": os.getenv("ACCESS_TOKEN"),
        "refresh_token": os.getenv("REFRESH_TOKEN")
    }



def renovar_token():
    """Renova o token de acesso do Mercado Livre."""
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

    print("✅ Token atualizado com sucesso.")
    return new_tokens["access_token"]


def get_access_token():
    """Obtém o token de acesso atual."""
    tokens = carregar_tokens()
    return tokens.get("access_token")


# ================================================================
# 🚴 ROTAS FLASK
# ================================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "🚴 API Fiorilli Bike Shop ativa!",
        "endpoints": ["/produtos", "/produto/<id>", "/buscar?q=..."]
    }), 200


# ================================================================
# 📦 ROTA - PRODUTOS (lê de produtos.json)
# ================================================================
@app.route("/produtos", methods=["GET"])
def produtos():
    """
    Retorna os produtos a partir do arquivo produtos.json.
    Se não existir, tenta buscá-los pela API do Mercado Livre.
    """
    try:
        caminho = os.path.join(os.path.dirname(__file__), "produtos.json")

        if not os.path.exists(caminho):
            app.logger.warning(f"⚠️ produtos.json não encontrado em {caminho}.")
            return jsonify({
                "erro": "Arquivo produtos.json não encontrado",
                "caminho_tentado": caminho
            }), 404

        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return jsonify(dados), 200

    except Exception as e:
        app.logger.error(f"❌ Erro ao carregar produtos: {e}")
        return jsonify({"erro": f"Falha ao carregar produtos: {str(e)}"}), 500


# ================================================================
# 🔍 ROTA - LISTAR PRODUTOS (API Mercado Livre)
# ================================================================
@app.route("/listar", methods=["GET"])
def listar_produtos():
    """
    Busca todos os produtos da conta do Mercado Livre (com paginação),
    salva localmente em produtos.json e retorna o catálogo atualizado.
    """
    try:
        token = get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        produtos = []
        limit = 50  # máximo permitido pela API
        offset = 0

        while True:
            url = f"https://api.mercadolibre.com/users/{SELLER_ID}/items/search?limit={limit}&offset={offset}"
            r = requests.get(url, headers=headers)

            # Se o token expirou, renova automaticamente
            if r.status_code == 401:
                token = renovar_token()
                headers["Authorization"] = f"Bearer {token}"
                r = requests.get(url, headers=headers)

            r.raise_for_status()
            dados = r.json()
            resultados = dados.get("results", [])

            if not resultados:
                break  # sem mais produtos

            for item_id in resultados:
                info = requests.get(f"https://api.mercadolibre.com/items/{item_id}", headers=headers).json()
                produtos.append({
                    "id": info.get("id"),
                    "nome": info.get("title"),
                    "preco": info.get("price"),
                    "estoque": info.get("available_quantity"),
                    "categoria": info.get("category_id"),
                    "link": info.get("permalink")
                })

            offset += limit

            # Segurança contra loop infinito
            if offset > 2000:
                app.logger.warning("⚠️ Limite de 2000 produtos atingido (paginador interrompido).")
                break

        # Caminho absoluto do arquivo produtos.json
        caminho = os.path.join(os.path.dirname(__file__), "produtos.json")

        # Salva o catálogo completo localmente
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(produtos, f, indent=2, ensure_ascii=False)

        app.logger.info(f"✅ Catálogo salvo em {caminho} ({len(produtos)} produtos).")

        return jsonify({
            "mensagem": f"{len(produtos)} produtos atualizados e salvos com sucesso!",
            "arquivo": "produtos.json",
            "produtos": produtos
        }), 200

    except Exception as e:
        app.logger.error(f"❌ Erro em listar_produtos: {e}")
        return jsonify({"erro": f"Falha ao listar produtos: {str(e)}"}), 500



# ================================================================
# 📄 ROTA - DETALHES DE UM PRODUTO
# ================================================================
@app.route("/produto/<id>", methods=["GET"])
def obter_produto(id):
    """Retorna os detalhes de um produto específico."""
    try:
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

    except Exception as e:
        app.logger.error(f"❌ Erro em obter_produto: {e}")
        return jsonify({"erro": f"Falha ao obter produto: {str(e)}"}), 500


# ================================================================
# 🔎 ROTA - BUSCAR PRODUTO POR TERMO
# ================================================================
@app.route("/buscar", methods=["GET"])
def buscar_produto():
    """Busca produtos pelo nome diretamente na API do Mercado Livre."""
    try:
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

        r.raise_for_status()
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

    except Exception as e:
        app.logger.error(f"❌ Erro em buscar_produto: {e}")
        return jsonify({"erro": f"Falha ao buscar produtos: {str(e)}"}), 500


# ================================================================
# 🚀 EXECUÇÃO LOCAL
# ================================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
