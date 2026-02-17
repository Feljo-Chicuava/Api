from http.server import BaseHTTPRequestHandler
import json
import yt_dlp
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        url = query.get('url', [None])[0]
        key = query.get('key', [None])[0]
        format_type = query.get('format', ['best'])[0]
        
        CHAVE_MESTRA = "0099@"

        # 1. Segurança
        if key != CHAVE_MESTRA:
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": "Chave invalida"}).encode())
            return

        if not url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": "URL ausente"}).encode())
            return

        # 2. Configuração yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best' if format_type == 'mp3' else 'best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Pega o link direto
                download_url = info.get('url')
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                resposta = {
                    "sucesso": True,
                    "dados": {
                        "id": info.get('id'),
                        "titulo": info.get('title'),
                        "thumb": info.get('thumbnail'),
                        "download": download_url
                    }
                }
                self.wfile.write(json.dumps(resposta).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": str(e)}).encode())
