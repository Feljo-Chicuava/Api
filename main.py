from fastapi import FastAPI, Query, HTTPException
from bs4 import BeautifulSoup
import httpx
import asyncio

app = FastAPI(title="Stream+ API Otimizada")

# URL base extraída do seu código original
BASE_URL = "https://hyper.hyperappz.site/"

# Configuração de Headers para evitar bloqueios
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# Cliente HTTP global e assíncrono
client = httpx.AsyncClient(headers=HEADERS, timeout=10.0, follow_redirects=True)

def parse_item(element):
    """Extrai dados de cada card de filme/série (Padrão do site)"""
    try:
        # Extração de ID e Link
        link_tag = element.select_one("div.poster a")
        link = link_tag.get('href', '') if link_tag else ""
        
        # Extração de Imagem
        img_tag = element.select_one("div.poster img")
        imagem = img_tag.get('src') if img_tag else ""
        
        # Extração de Título
        title_tag = element.select_one("div.data h3 a")
        titulo = title_tag.get_text(strip=True) if title_tag else ""
        
        # Extração de Avaliação e Ano
        rating = element.select_one("div.rating").get_text(strip=True) if element.select_one("div.rating") else "0"
        ano = element.select_one("div.data span").get_text(strip=True) if element.select_one("div.data span") else ""

        return {
            "id": element.get('id', '').replace('post-', ''),
            "titulo": titulo,
            "imagem": imagem,
            "rating": rating,
            "ano": ano,
            "link": link,
            "tipo": "Serie" if "/tvshows/" in link else "Filme"
        }
    except Exception:
        return None

@app.get("/")
async def home():
    """Rota que traz tudo: Animes, Novelas, Doramas e Séries Recentes"""
    try:
        response = await client.get(BASE_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        resumo = {
            "animes": [parse_item(i) for i in soup.select("#genre_animes article") if parse_item(i)],
            "novelas": [parse_item(i) for i in soup.select("#genre_novelas article") if parse_item(i)],
            "doramas": [parse_item(i) for i in soup.select("#genre_doramas-dramas-coreanos article") if parse_item(i)],
            "series": [parse_item(i) for i in soup.select("#dt-tvshows article") if parse_item(i)]
        }
        return resumo
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search(q: str = Query(..., description="Nome do filme ou série")):
    """Rota de Pesquisa Otimizada"""
    url = f"{BASE_URL}?s={q}"
    response = await client.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = [parse_item(i) for i in soup.select("article.item") if parse_item(i)]
    return {"query": q, "total": len(results), "results": results}

@app.get("/details")
async def details(url: str):
    """Rota para pegar o Player e a Descrição do conteúdo"""
    try:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tenta pegar o iframe do player
        iframe = soup.select_one("iframe.metaframe")
        player = iframe.get('src') if iframe else None
        
        # Descrição
        sinopse = soup.select_one("div.wp-content p")
        
        return {
            "titulo": soup.select_one("h1").get_text(strip=True) if soup.select_one("h1") else "Sem título",
            "sinopse": sinopse.get_text(strip=True) if sinopse else "",
            "player_url": player,
            "background": soup.select_one("div.poster img").get('src') if soup.select_one("div.poster img") else ""
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail="URL inválida ou erro no scraping")

# Fechar o cliente ao encerrar a API
@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()
