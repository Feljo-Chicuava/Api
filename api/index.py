from http.server import BaseHTTPRequestHandler
import json
import urllib.request
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        url_video = query.get('url', [None])[0]
        key = query.get('key', [None])[0]
        
        # 1. Filtro de Segurança Relâmpago
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
            # 2. Uso de API de extração direta (sem fila de espera/conversão)
            # Esta API foca em pegar o stream direto do servidor do YouTube
            encoded_url = urllib.parse.quote(url_video)
            # Usando um endpoint de alta disponibilidade
            api_fast = f"https://api.cobalt.tools/api/json"
            
            data = json.dumps({"url": url_video, "vQuality": "720"}).encode('utf-8')
            req = urllib.request.Request(
                api_fast, 
                data=data,
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0'
                }
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode())
                
                # Se a Cobalt falhar ou estiver saturada, o link direto estará em 'url'
                download_url = res_data.get('url') or res_data.get('picker', [{}])[0].get('url')

            if download_url:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(json.dumps({
                    "sucesso": True,
                    "velocidade": "ultra",
                    "dados": {
                        "download": download_url,
                        "origem": "direct-stream"
                    }
                }).encode())
            else:
                raise Exception("Não foi possível capturar o stream direto.")

        except Exception as e:
            # Fallback rápido para o método anterior caso o stream direto falhe
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": "IP Bloqueado ou API Offline"}).encode())
