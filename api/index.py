from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse
import time
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        url_video = query.get('url', [None])[0]
        key = query.get('key', [None])[0]
        fmt = query.get('format', ['mp3'])[0]
        
        if key != "0099@":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": "Chave invalida"}).encode())
            return

        if not url_video:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": "URL ausente"}).encode())
            return

        try:
            # 1. Inicia a conversão em uma API externa que lida com os bloqueios
            api_url = f"https://loader.to/ajax/download.php?format={fmt}&url={urllib.parse.quote(url_video)}"
            
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())

            if not data.get('id'):
                raise Exception("Servidor de conversao ocupado.")

            job_id = data['id']
            download_url = None

            # 2. Loop de progresso (Checa se ficou pronto)
            for _ in range(10):
                time.sleep(2)
                check_url = f"https://loader.to/ajax/progress.php?id={job_id}"
                with urllib.request.urlopen(check_url) as check_res:
                    check_data = json.loads(check_res.read().decode())
                    if check_data.get('success') and check_data.get('download_url'):
                        download_url = check_data['download_url']
                        break

            if download_url:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "sucesso": True,
                    "dados": {
                        "titulo": data.get('title', 'Video'),
                        "download": download_url
                    }
                }).encode())
            else:
                raise Exception("Tempo esgotado no processamento.")

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": str(e)}).encode())
