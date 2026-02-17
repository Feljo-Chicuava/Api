from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from youtubesearchpython import VideosSearch

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Configuração de resposta
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Pegar parâmetro 'q'
        query_params = parse_qs(urlparse(self.path).query)
        q = query_params.get('q', [''])[0]

        if not q:
            self.wfile.write(json.dumps({"status": "error", "message": "Query 'q' is missing"}).encode())
            return

        try:
            # Executa a busca
            search = VideosSearch(q, limit=5)
            # Retorna o resultado formatado
            self.wfile.write(json.dumps(search.result()).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"status": "error", "details": str(e)}).encode())
