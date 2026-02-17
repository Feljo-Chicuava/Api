export default async function handler(req, res) {
    // Configuração de Headers CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Content-Type', 'application/json');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    const { key, url, id, format = 'mp3' } = req.query;
    const CHAVE_MESTRA = "0099@";

    // 1. Validação de Segurança
    if (key !== CHAVE_MESTRA) {
        return res.status(401).json({ sucesso: false, erro: "Chave inválida." });
    }

    const input = url || id;
    if (!input) {
        return res.status(400).json({ sucesso: false, erro: "URL ou ID ausente." });
    }

    // 2. Regex para extrair o ID do vídeo (mesma lógica do seu PHP)
    const pattern = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^"&?\/ ]{11})/i;
    const match = input.match(pattern);
    const videoId = match ? match[1] : (input.trim().length === 11 ? input.trim() : null);

    if (!videoId) {
        return res.status(400).json({ sucesso: false, erro: "Link do YouTube não reconhecido." });
    }

    try {
        // 3. Iniciar conversão na API externa
        // Nota: Mantive o truque do googleusercontent que estava no seu código original
        const cleanUrl = `http://googleusercontent.com/youtube.com/v=${videoId}`;
        const startRes = await fetch(`https://loader.to/ajax/download.php?format=${format}&url=${encodeURIComponent(cleanUrl)}`);
        const startData = await startRes.json();

        if (!startData.id) {
            return res.status(503).json({ sucesso: false, erro: "Servidor externo ocupado." });
        }

        const jobId = startData.id;
        let downloadUrl = null;

        // 4. Loop de checagem (Polling) - Máximo 15 segundos
        for (let i = 0; i < 10; i++) {
            await new Promise(resolve => setTimeout(resolve, 1500)); // Espera 1.5s
            
            const checkRes = await fetch(`https://loader.to/ajax/progress.php?id=${jobId}`);
            const checkData = await checkRes.json();

            if (checkData.success && checkData.download_url) {
                downloadUrl = checkData.download_url;
                break;
            }
        }

        // 5. Resposta Final
        if (downloadUrl) {
            return res.status(200).json({
                sucesso: true,
                dados: {
                    id: videoId,
                    titulo: startData.title || "Vídeo do YouTube",
                    formato: format,
                    thumb: `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`,
                    download: downloadUrl
                }
            });
        } else {
            return res.status(408).json({ sucesso: false, erro: "O processamento demorou muito." });
        }

    } catch (error) {
        return res.status(500).json({ sucesso: false, erro: "Erro interno: " + error.message });
    }
}
