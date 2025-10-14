from flask import Flask, jsonify
import json

app = Flask(__name__)

@app.route("/")
def home():
    return "🚴 Servidor Fiorilli Bike Shop ativo! Acesse /produtos para ver o catálogo."

@app.route("/produtos")
def produtos():
    with open("../produtos.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == "__main__":
    app.run(port=5000)
