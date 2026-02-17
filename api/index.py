from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from youtube_search import YoutubeSearch

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Configurar cabeçalhos para JSON e CORS (para funcionar em frontends)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # 2. Pegar o termo de pesquisa da URL (ex: ?q=python)
        query_components = parse_qs(urlparse(self.path).query)
        search_query = query_components.get('q', [''])[0]

        # 3. Se não houver termo, retorne erro ou lista vazia
        if not search_query:
            self.wfile.write(json.dumps({"erro": "Faltou o parametro ?q="}).encode('utf-8'))
            return

        try:
            # 4. Realizar a pesquisa (limite de 10 videos para ser rapido)
            results = YoutubeSearch(search_query, max_results=10).to_dict()
            
            # 5. Enviar a resposta
            self.wfile.write(json.dumps(results).encode('utf-8'))
            
        except Exception as e:
            self.wfile.write(json.dumps({"erro": str(e)}).encode('utf-8'))

    return
