from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# URL extraída da lógica de descriptografia do seu código Java
BASE_URL = "SUA_URL_AQUI" 

def extrair_item(s):
    [cite_start]"""Replica a função 'extrair' do seu código Java [cite: 47-53]"""
    mapa = {}
    
    # [cite_start]ID: s.attr("id").replace("post-", "")[span_0](end_span)[span_1](end_span)
    mapa['id'] = s.get('id', '').replace('post-', '')
    
    # [span_2](start_span)[span_3](start_span)Imagem: div.poster img -> src[span_2](end_span)[span_3](end_span)
    img_tag = s.select_one('div.poster img')
    mapa['imagem'] = img_tag.get('src') if img_tag else ""
    
    # [span_4](start_span)[span_5](start_span)Rating: div.rating[span_4](end_span)[span_5](end_span)
    rating_tag = s.select_one('div.rating')
    mapa['rating'] = rating_tag.text.strip() if rating_tag else ""
    
    # [span_6](start_span)[span_7](start_span)Link e Tipo: Verifica se contém /trailer-m/ ou /trailer-s/ [cite: 52-53, 79-80]
    play_link = s.select_one('div.poster a')
    link = play_link.get('href') if play_link else ""
    mapa['link'] = link
    
    if "/trailer-m/" in link:
        mapa['tipo'] = "Filme"
    elif "/trailer-s/" in link:
        mapa['tipo'] = "Série"
    else:
        mapa['tipo'] = "Desconhecido"
    
    # [cite_start]Título: div.data h3 a [cite: 50-51, 77-78]
    titulo_tag = s.select_one('div.data h3 a')
    mapa['titulo'] = titulo_tag.text.strip() if titulo_tag else ""
    
    # [cite_start]Data: div.data span[span_6](end_span)[span_7](end_span)
    data_tag = s.select_one('div.data span')
    mapa['data'] = data_tag.text.strip() if data_tag else ""
    
    return mapa

@app.route('/api/home', methods=['GET'])
def home():
    try:
        response = requests.get(BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # [span_8](start_span)Mapeamento de todas as secções do seu HomeFragment [cite: 54-58]
        data = {
            "animes": [extrair_item(s) for s in soup.select('div#genre_animes article.item')],
            "novelas": [extrair_item(s) for s in soup.select('div#genre_novelas article.item')],
            "doramas": [extrair_item(s) for s in soup.select('div#genre_doramas-dramas-coreanos article.item')],
            "series_recentes": [extrair_item(s) for s in soup.select('div#dt-tvshows article.item')],
            "geral": [extrair_item(s) for s in soup.select('article.item')]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/generos', methods=['GET'])
def generos():
    [cite_start]"""Replica o _gener_request_listener [cite: 65-70]"""
    try:
        # [cite_start]No seu código, géneros usa uma URL com sufixo descriptografado[span_8](end_span)
        url_generos = BASE_URL + "/generos" # Ajuste conforme necessário
        response = requests.get(url_generos, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        lista_generos = []
        for g in soup.select('a.btgenre'):
            nome = g.text.strip()
            style = g.get('style', '')
            
            # [span_9](start_span)Extração da imagem via style url('...')[span_9](end_span)
            imagem = ""
            if "url('" in style:
                imagem = style.split("url('")[1].split("')")[0]
            
            # [span_10](start_span)Lógica de tipo de género[span_10](end_span)
            tipo_genero = "simples"
            nome_low = nome.lower()
            if "ano" in nome_low: tipo_genero = "porano"
            elif "coleções" in nome_low: tipo_genero = "colecoes"
            elif "legendados" in nome_low: tipo_genero = "legendado"
            elif "doramas" in nome_low: tipo_genero = "doramas"
            elif "animes" in nome_low: tipo_genero = "animes"
            
            lista_generos.append({
                "nome": nome,
                "link": g.get('href'),
                "imagem": imagem,
                "tipo": tipo_genero
            })
        return jsonify(lista_generos)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
