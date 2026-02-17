from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Aceita qualquer requisição de qualquer origem

CHAVE_MESTRA = "0099@"

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # 1. Validação da Chave
    key = request.args.get('key')
    if key != CHAVE_MESTRA:
        return jsonify({"erro": "Acesso negado. Chave invalida."}), 403

    # 2. Parâmetros
    input_val = request.args.get('url') or request.args.get('id')
    formato = request.args.get('format', 'mp3')

    if not input_val:
        return jsonify({"erro": "Parametro 'url' ou 'id' ausente."}), 400

    # Trata ID de 11 caracteres
    url = f"https://www.youtube.com/watch?v={input_val}" if len(input_val) == 11 else input_val

    # 3. Chamada Instantânea (Sem loop de espera)
    api_url = "https://loader.to/ajax/download.php"
    params = {'format': formato, 'url': url}
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        res = requests.get(api_url, params=params, headers=headers, timeout=5)
        data = res.json()

        if 'id' in data:
            return jsonify({
                "sucesso": True,
                "id_processamento": data['id'],
                "titulo": data.get('title', 'Video'),
                "check_url": f"https://loader.to/ajax/progress.php?id={data['id']}"
            })
        return jsonify({"erro": "Erro na API de origem", "detalhe": data}), 500
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
