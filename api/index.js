import youtubeDl from 'youtube-dl-exec';

export default async function handler(req, res) {
    // Headers para permitir acesso de qualquer lugar (CORS)
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');

    const { key, url, format = 'best' } = req.query;
    const CHAVE_MESTRA = "0099@";

    // 1. Segurança
    if (key !== CHAVE_MESTRA) {
        return res.status(401).json({ sucesso: false, erro: "Chave inválida." });
    }

    if (!url) {
        return res.status(400).json({ sucesso: false, erro: "Envie uma URL do YouTube." });
    }

    try {
        // 2. Execução do yt-dlp (apenas extração de metadados e links)
        const output = await youtubeDl(url, {
            dumpSingleJson: true,
            noCheckCertificates: true,
            noWarnings: true,
            preferFreeFormats: true,
            // Simula um bot do Google para tentar evitar bloqueios de IP
            addHeader: ['referer:youtube.com', 'user-agent:googlebot']
        });

        // 3. Filtrar o melhor link de download baseado no formato
        // Se pedir mp3, tentamos pegar o melhor áudio, senão o melhor vídeo
        const isAudio = format === 'mp3';
        const downloadUrl = isAudio 
            ? output.formats.filter(f => f.vcodec === 'none').pop()?.url 
            : output.url;

        // 4. Resposta formatada
        return res.status(200).json({
            sucesso: true,
            dados: {
                id: output.id,
                titulo: output.title,
                duracao: output.duration_string,
                thumb: output.thumbnail,
                canal: output.uploader,
                download: downloadUrl || output.url,
                formato_solicitado: format
            }
        });

    } catch (error) {
        console.error(error);
        return res.status(500).json({ 
            sucesso: false, 
            erro: "Erro ao processar vídeo. O YouTube pode ter bloqueado o IP temporariamente.",
            detalhes: error.message 
        });
    }
}
