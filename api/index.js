import youtubeDl from 'youtube-dl-exec';

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');

    const { key, url, format = 'best' } = req.query;
    const CHAVE_MESTRA = "0099@";

    if (key !== CHAVE_MESTRA) {
        return res.status(401).json({ sucesso: false, erro: "Chave inválida." });
    }

    if (!url) {
        return res.status(400).json({ sucesso: false, erro: "URL ausente." });
    }

    try {
        const output = await youtubeDl(url, {
            dumpSingleJson: true,
            noCheckCertificates: true,
            noWarnings: true,
            // Importante: evita que o yt-dlp tente usar pastas proibidas na Vercel
            cacheDir: '/tmp/youtube-dl-cache', 
            addHeader: ['referer:http://googleusercontent.com/youtube.com/6', 'user-agent:googlebot']
        });

        // Tenta pegar o link direto de áudio ou vídeo
        const downloadUrl = output.formats
            .filter(f => format === 'mp3' ? f.vcodec === 'none' : f.acodec !== 'none')
            .pop()?.url || output.url;

        return res.status(200).json({
            sucesso: true,
            dados: {
                id: output.id,
                titulo: output.title,
                thumb: output.thumbnail,
                download: downloadUrl
            }
        });

    } catch (error) {
        return res.status(500).json({ 
            sucesso: false, 
            erro: "Erro no yt-dlp", 
            detalhes: error.message 
        });
    }
}
