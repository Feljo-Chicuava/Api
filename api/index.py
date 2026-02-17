from http.server import BaseHTTPRequestHandler
import json
import re
from urllib.parse import urlparse, parse_qs
import yt_dlp

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Configurações de resposta
        query = parse_qs(urlparse(self.path).query)
        input_data = query.get('url', query.get('id', [None]))[0]
        key_enviada = query.get('key', [None])[0]
        formato = query.get('format', ['mp3'])[0]
        
        # 1. SEGURANÇA (Igual ao seu PHP)
        CHAVE_MESTRA = "0099@"
        if key_enviada != CHAVE_MESTRA:
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": "Chave inválida."}).encode())
            return

        # 2. EXTRAIR ID (Função pegarID adaptada)
        def pegar_id(text):
            if not text: return None
            pattern = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^"&?\/ ]{11})'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
            return text if len(text.strip()) == 11 else None

        video_id = pegar_id(input_data)

        if not video_id:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": "Link do YouTube não reconhecido."}).encode())
            return

        # 3. EXTRAÇÃO ULTRA RÁPIDA
        # Em vez de esperar conversão externa, pegamos os dados reais do vídeo
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'bestaudio/best' if formato == 'mp3' else 'bestvideo+bestaudio/best',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                # Resposta Final
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                resposta = {
                    "sucesso": True,
                    "dados": {
                        "id": video_id,
                        "titulo": info.get('title', 'Vídeo do YouTube'),
                        "duracao": info.get('duration'),
                        "thumb": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                        "canal": info.get('uploader'),
                        "stream_url": info.get('url') # URL do stream direto, sem espera
                    }
                }
                self.wfile.write(json.dumps(resposta).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"sucesso": False, "erro": str(e)}).encode())
