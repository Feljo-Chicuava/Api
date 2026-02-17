from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from youtubesearchpython import VideosSearch

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        query_params = parse_qs(urlparse(self.path).query)
        q = query_params.get('q', [''])[0]

        if not q:
            self.wfile.write(json.dumps({"error": "Query 'q' missing"}).encode())
            return

        try:
            # Busca simples com limite de 5
            videos_search = VideosSearch(q, limit=5)
            # O .result() retorna o dicionário pronto
            self.wfile.write(json.dumps(videos_search.result()).encode('utf-8'))
        except Exception as e:
            # Isso vai nos mostrar se o erro mudou
            self.wfile.write(json.dumps({"status": "error", "details": str(e)}).encode('utf-8'))
