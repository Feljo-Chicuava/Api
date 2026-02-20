from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# URL fornecida pelo usuário
BASE_URL = "https://hyper.hyperappz.site"

def tratar_imagem(url):
    if url and "w185" in url:
        return url.replace("w185", "original")
    return url

def extrair_item(s):
    mapa = {}
    try:
        # ID do post
        mapa['id'] = s.get('id', '').replace('post-', '')
        
        # Imagem
        img_tag = s.select_one('div.poster img')
        img_url = img_tag.get('src') if img_tag else ""
        mapa['imagem'] = tratar_imagem(img_url)
        
        # Rating
        rating_tag = s.select_one('div.rating')
        mapa['rating'] = rating_tag.text.strip() if rating_tag else ""
        
        # Link e Tipo
        play_link = s.select_one('div.poster a')
        link = play_link.get('href') if play_link else ""
        mapa['link'] = link
        
        if "/trailer-m/" in link:
            mapa['tipo'] = "Filme"
        elif "/trailer-s/" in link:
            mapa['tipo'] = "Série"
        else:
            mapa['tipo'] = "Conteúdo"
        
        # Título
        titulo_tag = s.select_one('div.data h3 a')
        mapa['titulo'] = titulo_tag.text.strip() if titulo_tag else ""
        
        # Ano
        data_tag = s.select_one('div.data span')
        mapa['data'] = data_tag.text.strip() if data_tag else ""
        
    except Exception:
        pass
    return mapa

@app.route('/')
def health():
    return jsonify({"status": "API Online", "fonte": BASE_URL})

@app.route('/api/home', methods=['GET'])
def home():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(BASE_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        data = {
            "animes": [extrair_item(s) for s in soup.select('div#genre_animes article.item')],
            "novelas": [extrair_item(s) for s in soup.select('div#genre_novelas article.item')],
            "doramas": [extrair_item(s) for s in soup.select('div#genre_doramas-dramas-coreanos article.item')],
            "series_recentes": [extrair_item(s) for s in soup.select('div#dt-tvshows article.item')],
            "lancamentos": [extrair_item(s) for s in soup.select('article.item')]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/generos', methods=['GET'])
def generos():
    try:
        response = requests.get(f"{BASE_URL}/generos", timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        lista_generos = []
        for g in soup.select('a.btgenre'):
            style = g.get('style', '')
            img_bg = ""
            if "url('" in style:
                img_bg = style.split("url('")[1].split("')")[0]
            elif "url(" in style:
                img_bg = style.split("url(")[1].split(")")[0].replace('"', '').replace("'", "")
                
            lista_generos.append({
                "nome": g.text.strip(),
                "link": g.get('href'),
                "imagem_fundo": img_bg
            })
        return jsonify(lista_generos)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# Export para o Vercel
app = app
