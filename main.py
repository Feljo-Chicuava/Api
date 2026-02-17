from fastapi import FastAPI, Query, HTTPException
from bs4 import BeautifulSoup
import httpx
import asyncio

app = FastAPI(title="Stream+ Lite API", description="API de Scraping Otimizada")

[span_6](start_span)BASE_URL = "https://hyper.hyperappz.site/" # Base extraída do código[span_6](end_span)

# Cliente HTTP assíncrono para maior velocidade
client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

def extrair_item(s):
    [span_7](start_span)"""Função auxiliar para extrair dados de artigos (mesma lógica do Java)[span_7](end_span)"""
    try:
        id_post = s.get('id', '').replace('post-', '')
        img_tag = s.select_one("div.poster img")
        imagem = img_tag.get('src') if img_tag else ""
        
        rating_tag = s.select_one("div.rating")
        rating = rating_tag.get_text(strip=True) if rating_tag else ""
        
        play_link = s.select_one("div.poster a")
        link = play_link.get('href', '') if play_link else ""
        
        titulo_tag = s.select_one("div.data h3 a")
        titulo = titulo_tag.get_text(strip=True) if titulo_tag else ""
        
        data_tag = s.select_one("div.data span")
        data_lanc = data_tag.get_text(strip=True) if data_tag else ""
        
        tipo = "Filme" if "/trailer-m/" in link else "Série" if "/trailer-s/" in link else "Desconhecido"
        
        return {
            "id": id_post,
            "titulo": titulo,
            "imagem": imagem,
            "rating": rating,
            "data": data_lanc,
            "link": link,
            "tipo": tipo
        }
    except:
        return None

@app.get("/")
async def home():
    [span_8](start_span)"""Rota principal: Animes, Novelas, Doramas e Séries[span_8](end_span)"""
    response = await client.get(BASE_URL)
    doc = BeautifulSoup(response.text, 'html.parser')
    
    return {
        "animes": [extrair_item(s) for s in doc.select("div#genre_animes article.item") if extrair_item(s)],
        "novelas": [extrair_item(s) for s in doc.select("div#genre_novelas article.item") if extrair_item(s)],
        "doramas": [extrair_item(s) for s in doc.select("div#genre_doramas-dramas-coreanos article.item") if extrair_item(s)],
        "series_recentes": [extrair_item(s) for s in doc.select("div#dt-tvshows article.item") if extrair_item(s)]
    }

@app.get("/search")
async def search(q: str = Query(..., min_length=1)):
    [span_9](start_span)"""Rota de Pesquisa[span_9](end_span)"""
    url = f"{BASE_URL}?s={q}"
    response = await client.get(url)
    doc = BeautifulSoup(response.text, 'html.parser')
    items = [extrair_item(s) for s in doc.select("article.item") if extrair_item(s)]
    return {"results": items}

@app.get("/details")
async def details(url: str):
    [span_10](start_span)[span_11](start_span)[span_12](start_span)"""Rota de Detalhes (Extrai Player, Descrição, etc)[span_10](end_span)[span_11](end_span)[span_12](end_span)"""
    response = await client.get(url)
    doc = BeautifulSoup(response.text, 'html.parser')
    
    # Nome e Descrição
    nome = doc.select_one("h1").text if doc.select_one("h1") else ""
    descricao = doc.select_one("div.wp-content p").text if doc.select_one("div.wp-content p") else ""
    
    # [span_13](start_span)Player URL (Otimizado)[span_13](end_span)
    player_url = ""
    iframe = doc.select_one("iframe.metaframe.rptss")
    if iframe:
        player_url = iframe.get('src')
    
    return {
        "nome": nome,
        "descricao": descricao,
        "player_url": player_url,
        "poster": doc.select_one("div.poster img").get('src') if doc.select_one("div.poster img") else ""
    }
