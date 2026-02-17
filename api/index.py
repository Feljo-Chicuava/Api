from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from youtubesearchpython import VideosSearch # Biblioteca atualizada

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        query_components = parse_qs(urlparse(self.path).query)
        search_query = query_components.get('q', [''])[0]

        if not search_query:
            self.wfile.write(json.dumps({"erro": "Busca vazia"}).encode('utf-8'))
            return

        try:
            # Nova forma de buscar
            videos_search = VideosSearch(search_query, limit = 10)
            results = videos_search.result()
            
            self.wfile.write(json.dumps(results).encode('utf-8'))
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
