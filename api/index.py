from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

BASE_URL = "https://hyper.hyperappz.site/"

def scrape_data(path):
    url = f"{BASE_URL}{path}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # [span_10](start_span)[span_11](start_span)[span_12](start_span)Seleciona elementos 'a' com a classe 'btgenre' como no Java[span_10](end_span)[span_11](end_span)[span_12](end_span)
        items = soup.select("a.btgenre")
        
        for item in items:
            link = item.get('href', '').strip()
            nome = item.get_text().strip()
            
            # [span_13](start_span)[span_14](start_span)[span_15](start_span)Extração da imagem do atributo 'style'[span_13](end_span)[span_14](end_span)[span_15](end_span)
            style = item.get('style', '')
            imagem = ""
            if "url('" in style:
                start = style.find("url('") + 5
                end = style.find("')", start)
                imagem = style[start:end].strip()
            
            results.append({
                "nome": nome,
                "link": link,
                "imagem": imagem
            })
            
        return results
    except Exception as e:
        return {"error": str(e)}

@app.route('/api/genres', methods=['GET'])
def get_genres():
    # [span_16](start_span)Rota baseada na FavoritesFragmentActivity[span_16](end_span)
    data = scrape_data("generos/")
    return jsonify(data)

@app.route('/api/scrape', methods=['GET'])
def custom_scrape():
    # [span_17](start_span)[span_18](start_span)[span_19](start_span)Permite passar o caminho dinamicamente[span_17](end_span)[span_18](end_span)[span_19](end_span)
    path = request.args.get('path', '')
    data = scrape_data(path)
    return jsonify(data)

@app.route('/')
def home():
    return "API de Scraping ativa."

if __name__ == '__main__':
    app.run(debug=True)
