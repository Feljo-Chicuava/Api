from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Aceita qualquer requisição (Cross-Origin)

# Configurações
CHAVE_MESTRA = "0099@"

@app.route('/api/index', methods=['GET', 'POST'])
def youtube_downloader():
    # 1. Verificação de Chave e Parâmetros
    key = request.args.get('key')
    if key != CHAVE_MESTRA:
        return jsonify({"erro": "Chave de API invalida"}), 403

    input_data = request.args.get('url') or request.args.get('id')
    formato = request.args.get('format', 'mp3')

    if not input_data:
        return jsonify({"erro": "Envie ?url= ou ?id= e &key=0099@"}), 400

    # Se for apenas o ID de 11 caracteres, monta a URL
    url = f"https://www.youtube.com/watch?v={input_data}" if len(input_data) == 11 else input_data

    # 2. Iniciar a Conversão (Rápido)
    api_start = "https://loader.to/ajax/download.php"
    params = {
        'format': formato,
        'url': url
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(api_start, params=params, headers=headers, timeout=10)
        data_start = response.json()

        if 'id' in data_start:
            # 3. Resultado Imediato sem o Loop de espera
            return jsonify({
                "sucesso": True,
                "mensagem": "Conversao iniciada!",
                "id_processamento": data_start['id'],
                "titulo": data_start.get('title', 'Video/Audio YouTube'),
                "url_verificacao": f"https://loader.to/ajax/progress.php?id={data_start['id']}"
            })
        else:
            return jsonify({
                "sucesso": False,
                "erro": "Falha ao iniciar conversao na API externa",
                "detalhe": data_start
            }), 500

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# Necessário para rodar localmente ou em certos ambientes
if __name__ == '__main__':
    app.run(debug=True)
