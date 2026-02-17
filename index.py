from fastapi import FastAPI, Query, HTTPException
from bs4 import BeautifulSoup
import httpx

app = FastAPI(title="Stream+ API")

# URL extraída do seu código Android
BASE_URL = "https://hyper.hyperappz.site/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9"
}

# Cliente HTTP otimizado
client = httpx.AsyncClient(headers=HEADERS, timeout=15.0, follow_redirects=True)

def parse_item(element):
    """Extrai os dados de cada bloco de conteúdo no site"""
    try:
        link_tag = element.select_one("div.poster a")
        link = link_tag.get('href', '') if link_tag else ""
        
        img_tag = element.select_one("div.poster img")
        # Pega o 'src' ou 'data-src' para evitar imagens vazias (lazy load)
        imagem = img_tag.get('src') or img_tag.get('data-src') or ""
        
        title_tag = element.select_one("div.data h3 a")
        titulo = title_tag.get_text(strip=True) if title_tag else ""
        
        rating = element.select_one("div.rating").get_text(strip=True) if element.select_one("div.rating") else "N/A"
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
    """Busca Animes, Novelas, Doramas e Séries da Home"""
    try:
        response = await client.get(BASE_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        return {
            "animes": [parse_item(i) for i in soup.select("#genre_animes article") if parse_item(i)],
            "novelas": [parse_item(i) for i in soup.select("#genre_novelas article") if parse_item(i)],
            "doramas": [parse_item(i) for i in soup.select("#genre_doramas-dramas-coreanos article") if parse_item(i)],
            "series": [parse_item(i) for i in soup.select("#dt-tvshows article") if parse_item(i)]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao servidor de origem.")

@app.get("/search")
async def search(q: str = Query(..., min_length=1)):
    """Pesquisa de conteúdos"""
    url = f"{BASE_URL}?s={q}"
    response = await client.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = [parse_item(i) for i in soup.select("article.item") if parse_item(i)]
    return {"results": results}

@app.get("/details")
async def details(url: str):
    """Extrai detalhes e o link do player para o app"""
    try:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procura o iframe do player (geralmente rptss ou metaframe)
        iframe = soup.select_one("iframe.metaframe, iframe.rptss")
        player = iframe.get('src') if iframe else None
        
        sinopse = soup.select_one("div.wp-content p")
        
        return {
            "titulo": soup.select_one("h1").get_text(strip=True) if soup.select_one("h1") else "",
            "sinopse": sinopse.get_text(strip=True) if sinopse else "",
            "player_url": player,
            "capa": soup.select_one("div.poster img").get('src') if soup.select_one("div.poster img") else ""
        }
    except Exception:
        raise HTTPException(status_code=400, detail="Erro ao extrair detalhes.")

@app.on_event("shutdown")
async def shutdown():
    await client.aclose()
