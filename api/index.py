# api/index.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Any
import concurrent.futures
from functools import lru_cache
import time

app = Flask(__name__)
CORS(app)

# Configurações
BASE_URL = "https://hyper.hyperappz.site"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
}

# Cache simples para respostas
cache = {}
CACHE_DURATION = 300  # 5 minutos

def get_cached_or_fetch(url):
    """Obtém dados do cache ou faz requisição"""
    current_time = time.time()
    
    if url in cache:
        data, timestamp = cache[url]
        if current_time - timestamp < CACHE_DURATION:
            return data
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        cache[url] = (response.text, current_time)
        return response.text
    except requests.RequestException as e:
        return None

def extract_movie_data(element) -> Dict[str, Any]:
    """Extrai dados de um filme/série do elemento HTML"""
    data = {}
    
    # ID
    data['id'] = element.get('id', '').replace('post-', '')
    
    # Imagem
    img = element.select_one('div.poster img')
    data['imagem'] = img.get('src', '') if img else ''
    
    # Título e link
    title_link = element.select_one('div.data h3 a')
    if title_link:
        data['titulo'] = title_link.text.strip()
        data['link'] = title_link.get('href', '')
    
    # Data
    span_data = element.select_one('div.data span')
    data['data'] = span_data.text.strip() if span_data else ''
    
    # Rating
    rating = element.select_one('div.rating')
    data['rating'] = rating.text.strip() if rating else ''
    
    # Tipo (Filme/Série)
    link = data.get('link', '')
    if '/trailer-m/' in link:
        data['tipo'] = 'Filme'
    elif '/trailer-s/' in link:
        data['tipo'] = 'Série'
    else:
        data['tipo'] = 'Desconhecido'
    
    # Extrair ano da data
    if data['data'] and len(data['data']) >= 4:
        match = re.search(r'\d{4}', data['data'])
        data['ano'] = match.group(0) if match else data['data'][-4:]
    else:
        data['ano'] = ''
    
    return data

def extract_genre_data(element) -> Dict[str, Any]:
    """Extrai dados de um gênero do elemento HTML"""
    data = {}
    
    data['nome'] = element.text.strip()
    data['link'] = element.get('href', '')
    
    # Extrair imagem do style
    style = element.get('style', '')
    if 'url(' in style:
        match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
        if match:
            data['imagem'] = match.group(1).strip()
    else:
        data['imagem'] = ''
    
    # Determinar tipo de gênero
    nome_lower = data['nome'].lower()
    if 'ano' in nome_lower or 'seleção por ano' in nome_lower:
        data['tipo_genero'] = 'porano'
    elif 'coleções' in nome_lower:
        data['tipo_genero'] = 'colecoes'
    elif 'legendados' in nome_lower:
        data['tipo_genero'] = 'legendado'
    elif 'doramas' in nome_lower:
        data['tipo_genero'] = 'doramas'
    elif 'animes' in nome_lower:
        data['tipo_genero'] = 'animes'
    else:
        data['tipo_genero'] = 'simples'
    
    return data

@app.route('/')
def home():
    """Rota inicial com informações da API"""
    return jsonify({
        'nome': 'Stream+ API',
        'versao': '1.0.0',
        'descricao': 'API para consulta de filmes e séries',
        'endpoints': {
            '/home': 'Dados da página inicial (destaques, lançamentos)',
            '/buscar?q=<termo>': 'Busca por filmes/séries',
            '/detalhes?url=<url>&tipo=<m/tv>': 'Detalhes de um filme ou série',
            '/generos': 'Lista todos os gêneros',
            '/genero?url=<url>': 'Lista itens de um gênero específico',
            '/ano?url=<url>': 'Lista itens por ano',
            '/colecoes?url=<url>': 'Lista coleções',
            '/legendados?url=<url>': 'Lista conteúdos legendados',
            '/player?url=<url>': 'Obtém link do player',
            '/relacionados?url=<url>': 'Conteúdos relacionados',
            '/tmdb/<tipo>/<id>': 'Dados do TMDb (movie/tv)'
        }
    })

@app.route('/home')
def get_home():
    """Obtém dados da página inicial"""
    html = get_cached_or_fetch(f"{BASE_URL}/")
    if not html:
        return jsonify({'erro': 'Não foi possível acessar o site'}), 500
    
    soup = BeautifulSoup(html, 'html.parser')
    
    result = {}
    
    # Lançamentos
    lancamentos = []
    for item in soup.select('article.item'):
        lancamentos.append(extract_movie_data(item))
    result['lancamentos'] = lancamentos[:20]
    
    # Animes
    animes = []
    for item in soup.select('div#genre_animes article.item'):
        animes.append(extract_movie_data(item))
    result['animes'] = animes[:20]
    
    # Novelas
    novelas = []
    for item in soup.select('div#genre_novelas article.item'):
        novelas.append(extract_movie_data(item))
    result['novelas'] = novelas[:20]
    
    # Doramas
    doramas = []
    for item in soup.select('div#genre_doramas-dramas-coreanos article.item'):
        doramas.append(extract_movie_data(item))
    result['doramas'] = doramas[:20]
    
    # Séries recentes
    series = []
    for item in soup.select('div#dt-tvshows article.item'):
        series.append(extract_movie_data(item))
    result['series_recentes'] = series[:20]
    
    return jsonify(result)

@app.route('/buscar')
def search():
    """Busca por filmes/séries"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'erro': 'Parâmetro "q" é obrigatório'}), 400
    
    html = get_cached_or_fetch(f"{BASE_URL}/?s={query}")
    if not html:
        return jsonify({'erro': 'Não foi possível acessar o site'}), 500
    
    soup = BeautifulSoup(html, 'html.parser')
    
    results = []
    for item in soup.select('div.result-item article'):
        data = extract_movie_data(item)
        
        # Extrair descrição
        desc = item.select_one('div.contenido p')
        if desc:
            data['descricao'] = desc.text.strip()
        
        results.append(data)
    
    return jsonify({
        'query': query,
        'resultados': results
    })

@app.route('/detalhes')
def get_details():
    """Obtém detalhes de um filme ou série"""
    url = request.args.get('url', '')
    tipo = request.args.get('tipo', 'm')  # m = filme, tv = série
    
    if not url:
        return jsonify({'erro': 'Parâmetro "url" é obrigatório'}), 400
    
    # Se a URL não for completa, adiciona o base
    if not url.startswith('http'):
        url = f"{BASE_URL}/{url.lstrip('/')}"
    
    html = get_cached_or_fetch(url)
    if not html:
        return jsonify({'erro': 'Não foi possível acessar a página'}), 500
    
    soup = BeautifulSoup(html, 'html.parser')
    
    result = {}
    
    # Título
    titulo = soup.select_one('h1')
    result['titulo'] = titulo.text.strip() if titulo else ''
    
    # Ano
    data_elem = soup.select_one('span.date')
    if data_elem:
        data_text = data_elem.text.strip()
        match = re.search(r'\d{4}', data_text)
        result['ano'] = match.group(0) if match else data_text
    else:
        result['ano'] = ''
    
    # Player
    iframe = soup.select_one('iframe.metaframe.rptss') or soup.select_one('iframe[src*="player.fimoo.site"]')
    result['player_url'] = iframe.get('src', '') if iframe else ''
    
    # Se não encontrou, procura outros iframes
    if not result['player_url']:
        for iframe in soup.select('iframe.rptss'):
            src = iframe.get('src', '')
            if 'youtube.com' not in src:
                result['player_url'] = src
                break
    
    # Descrição
    desc = soup.select_one('div.wp-content p')
    result['descricao'] = desc.text.strip() if desc else ''
    
    # Gêneros
    generos = []
    for gen in soup.select('div.sgeneros a'):
        generos.append(gen.text.strip())
    result['generos'] = generos
    
    # Nota
    nota = soup.select_one('span.dt_rating_vgs')
    result['nota'] = nota.text.strip() if nota else ''
    
    # Poster
    poster = soup.select_one('div.poster img')
    result['poster'] = poster.get('src', '') if poster else ''
    
    # Trailer (YouTube)
    trailer = ''
    for iframe in soup.select('iframe.rptss[src*="youtube.com"]'):
        trailer = iframe.get('src', '')
        break
    result['trailer'] = trailer
    
    return jsonify(result)

@app.route('/generos')
def get_genres():
    """Lista todos os gêneros"""
    html = get_cached_or_fetch(f"{BASE_URL}/generos/")
    if not html:
        return jsonify({'erro': 'Não foi possível acessar o site'}), 500
    
    soup = BeautifulSoup(html, 'html.parser')
    
    generos = []
    for gen in soup.select('a.btgenre'):
        generos.append(extract_genre_data(gen))
    
    # Agrupar por tipo
    result = {
        'todos': generos,
        'por_tipo': {}
    }
    
    for gen in generos:
        tipo = gen['tipo_genero']
        if tipo not in result['por_tipo']:
            result['por_tipo'][tipo] = []
        result['por_tipo'][tipo].append(gen)
    
    return jsonify(result)

@app.route('/genero')
def get_genre_items():
    """Lista itens de um gênero específico"""
    url = request.args.get('url', '')
    pagina = request.args.get('pagina', '1')
    
    if not url:
        return jsonify({'erro': 'Parâmetro "url" é obrigatório'}), 400
    
    if not url.startswith('http'):
        url = f"{BASE_URL}/{url.lstrip('/')}"
    
    if pagina != '1':
        url = f"{url.rstrip('/')}/page/{pagina}/"
    
    html = get_cached_or_fetch(url)
    if not html:
        return jsonify({'erro': 'Não foi possível acessar a página'}), 500
    
    soup = BeautifulSoup(html, 'html.parser')
    
    items = []
    for item in soup.select('article.item'):
        items.append(extract_movie_data(item))
    
    # Verificar se há próxima página
    next_page = soup.select_one('a.next.page-numbers')
    tem_proxima = next_page is not None
    
    return jsonify({
        'pagina': int(pagina),
        'tem_proxima': tem_proxima,
        'items': items
    })

@app.route('/ano')
def get_year_items():
    """Lista itens por ano"""
    url = request.args.get('url', '')
    
    if not url:
        return jsonify({'erro': 'Parâmetro "url" é obrigatório'}), 400
    
    if not url.startswith('http'):
        url = f"{BASE_URL}/{url.lstrip('/')}"
    
    html = get_cached_or_fetch(url)
    if not html:
        return jsonify({'erro': 'Não foi possível acessar a página'}), 500
    
    soup = BeautifulSoup(html, 'html.parser')
    
    anos = []
    for ano_elem in soup.select('a.btgenre'):
        data = extract_genre_data(ano_elem)
        
        # Extrair ano do texto
        ano_text = data['nome']
        match = re.search(r'\d{4}', ano_text)
        if match:
            data['ano'] = match.group(0)
        
        anos.append(data)
    
    return jsonify(anos)

@app.route('/colecoes')
def get_collections():
    """Lista coleções"""
    url = request.args.get('url', '')
    
    if not url:
        return jsonify({'erro': 'Parâmetro "url" é obrigatório'}), 400
    
    if not url.startswith('http'):
        url = f"{BASE_URL}/{url.lstrip('/')}"
    
    html = get_cached_or_fetch(url)
    if not html:
        return jsonify({'erro': 'Não foi possível acessar a página'}), 500
    
    soup = BeautifulSoup(html, 'html.parser')
    
    colecoes = []
    for col in soup.select('a.btgenre'):
        data = extract_genre_data(col)
        data['nome_colecao'] = data['nome']
        colecoes.append(data)
    
    return jsonify(colecoes)

@app.route('/legendados')
def get_subtitled():
    """Lista conteúdos legendados"""
    url = request.args.get('url', '')
    
    if not url:
        return jsonify({'erro': 'Parâmetro "url" é obrigatório'}), 400
    
    if not url.startswith('http'):
        url = f"{BASE_URL}/{url.lstrip('/')}"
    
    html = get_cached_or_fetch(url)
    if not html:
        return jsonify({'erro': 'Não foi possível acessar a página'}), 500
    
    soup = BeautifulSoup(html, 'html.parser')
    
    legendados = []
    for leg in soup.select('a.btgenre'):
        legendados.append(extract_genre_data(leg))
    
    return jsonify(legendados)

@app.route('/player')
def get_player():
    """Obtém link do player"""
    url = request.args.get('url', '')
    
    if not url:
        return jsonify({'erro': 'Parâmetro "url" é obrigatório'}), 400
    
    html = get_cached_or_fetch(url)
    if not html:
        return jsonify({'erro': 'Não foi possível acessar a página'}), 500
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Procurar por links de download
    download_links = []
    for link in soup.select('#down-list li a'):
        download_links.append({
            'texto': link.text.strip(),
            'url': link.get('href', '')
        })
    
    # Procurar por iframe do player
    iframe = soup.select_one('iframe[src*="player"]')
    player_url = iframe.get('src', '') if iframe else ''
    
    return jsonify({
        'player_url': player_url,
        'download_links': download_links
    })

@app.route('/relacionados')
def get_related():
    """Obtém conteúdos relacionados"""
    url = request.args.get('url', '')
    
    if not url:
        return jsonify({'erro': 'Parâmetro "url" é obrigatório'}), 400
    
    html = get_cached_or_fetch(url)
    if not html:
        return jsonify({'erro': 'Não foi possível acessar a página'}), 500
    
    soup = BeautifulSoup(html, 'html.parser')
    
    relacionados = []
    for rel in soup.select('div#single_relacionados article'):
        data = {}
        
        # Link
        link = rel.select_one('a')
        if link:
            data['link'] = link.get('href', '')
        
        # Imagem
        img = rel.select_one('img')
        if img:
            data['imagem'] = img.get('src', '')
            data['titulo'] = img.get('alt', '')
        
        # Tipo
        link_url = data.get('link', '')
        if '/trailer-m/' in link_url:
            data['tipo'] = 'Filme'
        elif '/trailer-s/' in link_url:
            data['tipo'] = 'Série'
        else:
            data['tipo'] = 'Desconhecido'
        
        relacionados.append(data)
    
    return jsonify(relacionados)

@app.route('/tmdb/<tipo>/<id>')
def get_tmdb(tipo, id):
    """Obtém dados do TMDb"""
    import requests
    
    api_key = 'a99eb83d7deb1f8e82b0d045c0a0a611'
    
    if tipo == 'movie':
        url = f"https://api.themoviedb.org/3/movie/{id}?api_key={api_key}&language=pt-BR&append_to_response=credits,videos"
    elif tipo == 'tv':
        url = f"https://api.themoviedb.org/3/tv/{id}?api_key={api_key}&language=pt-BR&append_to_response=credits,videos"
    else:
        return jsonify({'erro': 'Tipo inválido. Use "movie" ou "tv"'}), 400
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/buscar-tmdb')
def search_tmdb():
    """Busca no TMDb"""
    query = request.args.get('q', '')
    tipo = request.args.get('tipo', 'movie')  # movie ou tv
    ano = request.args.get('ano', '')
    
    if not query:
        return jsonify({'erro': 'Parâmetro "q" é obrigatório'}), 400
    
    import requests
    
    api_key = 'a99eb83d7deb1f8e82b0d045c0a0a611'
    
    if tipo == 'movie':
        url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}&language=pt-BR"
        if ano:
            url += f"&year={ano}"
    elif tipo == 'tv':
        url = f"https://api.themoviedb.org/3/search/tv?api_key={api_key}&query={query}&language=pt-BR"
        if ano:
            url += f"&first_air_date_year={ano}"
    else:
        return jsonify({'erro': 'Tipo inválido. Use "movie" ou "tv"'}), 400
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({'erro': str(e)}), 500

# Para Vercel, precisamos exportar a app como 'app'
# Em vez de executar diretamente
if __name__ == '__main__':
    app.run(debug=True)
else:
    # Para Vercel serverless
    pass
