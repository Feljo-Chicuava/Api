from http.server import BaseHTTPRequestHandler
import json
import re
import urllib.request
import urllib.parse
import time
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        path = self.path.split('?')[0]
        
        # 1. SEGURANÇA (Baseado no original)
        CHAVE_MESTRA = "0099@"
        key_enviada = query.get('key', [None])[0]
        
        if key_enviada != CHAVE_MESTRA:
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": "Chave inválida."}).encode())
            return

        # 2. LÓGICA DE EXTRAÇÃO DE ID
        def pegar_id(text):
            if not text: return None
            pattern = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^"&?\/ ]{11})'
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1) if match else (text if len(text.strip()) == 11 else None)

        input_url = query.get('url', query.get('id', [None]))[0]
        video_id = pegar_id(input_url)
        formato = query.get('format', ['mp3'])[0]

        if not video_id:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": "Link inválido."}).encode())
            return

        try:
            # 3. COMUNICAÇÃO COM O SERVIDOR (Simulando o original)
            url_limpa = f"https://www.youtube.com/watch?v={video_id}"
            api_start = f"https://loader.to/ajax/download.php?format={formato}&url={urllib.parse.quote(url_limpa)}"
            
            req = urllib.request.Request(api_start, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data_start = json.loads(response.read().decode())

            job_id = data_start.get('id')
            if not job_id:
                raise Exception("Servidor ocupado.")

            # 4. AGUARDANDO O LINK (Polling rápido)
            link_direto = None
            for _ in range(8): # Reduzido para ser mais rápido
                time.sleep(1.2)
                with urllib.request.urlopen(f"https://loader.to/ajax/progress.php?id={job_id}") as check:
                    res_check = json.loads(check.read().decode())
                    if res_check.get('success') and res_check.get('download_url'):
                        link_direto = res_check['download_url']
                        break

            if link_direto:
                # 5. RESPOSTA SEM LINK DIRETO
                # Criamos um link que aponta para a sua própria API
                host = self.headers.get('Host')
                proxy_download = f"https://{host}/api/download?file={urllib.parse.quote(link_direto)}"
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(json.dumps({
                    "sucesso": True,
                    "dados": {
                        "id": video_id,
                        "titulo": data_start.get('title', 'Vídeo'),
                        "thumb": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                        "download_api": proxy_download  # O link direto não aparece aqui
                    }
                }).encode())
            else:
                raise Exception("Tempo esgotado.")

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": str(e)}).encode())
