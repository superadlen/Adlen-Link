const { addonBuilder, serveHTTP } = require("stremio-addon-sdk");
const fetch = require("node-fetch");

// Liste des sources avec l'ajout de ThePirateBay+
const SOURCES = [
    { name: "Filmora", url: "https://filmora-production.up.railway.app/stream" },
    { name: "Peerflix", url: "https://addon.peerflix.mov/language=en%7Cqualityfilter=sd,480p,540p,hdtv,screener,vhs,unknown%7Csort=seed-desc,quality-desc,size-desc/stream" },
];

const manifest = {
    "id": "org.adlen.cinema",
    "version": "2.0.2",
    "name": "Nuvio-Link⚡",
    "description": "Hub DzMovie⚡ : Multi-sources Superadlen DZ Dev 2026.",
    "logo": "https://i.imgur.com/tW6p3Ch.png", 
    "resources": ["stream"],
    "types": ["movie", "series"],
    "idPrefixes": ["tt"],
    "catalogs": []
};

const builder = new addonBuilder(manifest);

// Fonction pour extraire proprement la qualité du titre
function getQuality(stream) {
    if (stream.quality) return stream.quality.toUpperCase();
    const title = stream.title || "";
    const qualityMatch = title.match(/(4K|2160p|1080p|720p|480p)/i);
    return qualityMatch ? qualityMatch[0].toUpperCase() : "HD";
}

// Utilitaire de conversion de taille
function formatBytes(bytes) {
    if (!bytes || bytes === 0) return "";
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Formateur de titre avancé
function formatTitle(stream) {
    let lines = [];
    let l1 = "";
    if (stream.quality) l1 += `🎥 ${stream.quality} `;
    if (stream.encode) l1 += `🎞️ ${stream.encode} `;
    if (stream.releaseGroup) l1 += `🏷️ ${stream.releaseGroup} `;
    if (l1) lines.push(l1.trim());

    let l3 = "";
    if (stream.size > 0) l3 += `📦 ${formatBytes(stream.size)} `;
    if (stream.seeders > 0) l3 += `👥 ${stream.seeders} `;
    if (l3) lines.push(l3.trim());

    if (stream.languages && stream.languages.length) lines.push(`🌎 ${stream.languages.join(' | ')}`);
    if (stream.filename) lines.push(`📁 ${stream.filename}`);

    return lines.length > 0 ? lines.join('\n') : stream.title;
}

builder.defineStreamHandler(async (args) => {
    const { type, id } = args;

    const requests = SOURCES.map(source => 
        fetch(`${source.url}/${type}/${id}.json`)
            .then(res => res.json())
            .then(data => {
                if (!data || !data.streams) return [];
                
                // Limite à 8 titres par source et renommage avec Qualité
                return data.streams.slice(0, 20).map(stream => {
                    const quality = getQuality(stream);
                    return {
                        ...stream,
                        name: `Nuvio 🎬: ${quality}`, 
                        title: formatTitle(stream)
                    };
                });
            })
            .catch(() => [])
    );

    try {
        const results = await Promise.all(requests);
        return { streams: results.flat() };
    } catch (error) {
        return { streams: [] };
    }
});

serveHTTP(builder.getInterface(), { port: process.env.PORT || 7000 });
console.log("🚀 Adlen-Cinema est prêt avec ThePirateBay+ !");
