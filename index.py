from fastapi import FastAPI, Query, HTTPException
from bs4 import BeautifulSoup
import httpx

app = FastAPI(title="Stream+ API")

# URL base
BASE_URL = "https://hyper.hyperappz.site/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

client = httpx.AsyncClient(headers=HEADERS, timeout=15.0, follow_redirects=True)

def parse_item(element):
    try:
        link_tag = element.select_one("div.poster a")
        link = link_tag.get('href', '') if link_tag else ""
        
        img_tag = element.select_one("div.poster img")
        imagem = img_tag.get('src') or img_tag.get('data-src') or ""
        
        title_tag = element.select_one("div.data h3 a")
        titulo = title_tag.get_text(strip=True) if title_tag else ""
        
        rating = element.select_one("div.rating").get_text(strip=True) if element.select_one("div.rating") else "N/A"
        
        return {
            "titulo": titulo,
            "imagem": imagem,
            "rating": rating,
            "link": link,
            "tipo": "Serie" if "/tvshows/" in link else "Filme"
        }
    except:
        return None

@app.get("/")
async def home():
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
        return {"erro": str(e)}

@app.get("/search")
async def search(q: str = Query(..., min_length=1)):
    url = f"{BASE_URL}?s={q}"
    response = await client.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return {"results": [parse_item(i) for i in soup.select("article.item") if parse_item(i)]}

@app.get("/details")
async def details(url: str):
    try:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        iframe = soup.select_one("iframe.metaframe, iframe.rptss")
        player = iframe.get('src') if iframe else None
        
        sinopse = soup.select_one("div.wp-content p")
        
        return {
            "titulo": soup.select_one("h1").get_text(strip=True) if soup.select_one("h1") else "",
            "sinopse": sinopse.get_text(strip=True) if sinopse else "",
            "player_url": player,
            "capa": soup.select_one("div.poster img").get('src') if soup.select_one("div.poster img") else ""
        }
    except:
        return {"erro": "Falha ao obter detalhes"}

@app.on_event("shutdown")
async def shutdown():
    await client.aclose()
