import os
import requests
import zipfile
import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# CONSEIL : Change cette clé si tu en as généré une nouvelle sur SubDL
API_KEY = "xF1Vsj1tXWPxG7PP59vS1sypy_N_ETxZ"
BASE_URL = "https://api.subdl.com/api/v1/subtitles"
HF_PUBLIC_URL = "https://superadlen-dz-arabic.hf.space"

MANIFEST = {
    "id": "com.adlen.arabic.subtitles",
    "version": "2.0.0",
    "name": "DZ-Arabic",
    "description": "Arabic Subtitles By Superadlen - Dz Devloper  ترجمة عربية للكل",
    "logo": "https://i.imgur.com/o1hZxni.png",
    "types": ["movie", "series"],
    "catalogs": [],
    "resources": ["subtitles"],
    "idPrefixes": ["tt", "tmdb"]
}

@app.route('/')
def root():
    return jsonify(MANIFEST)

@app.route('/manifest.json')
def get_manifest():
    return jsonify(MANIFEST)

@app.route('/subtitles/<type>/<path:extra_path>')
def get_subtitles(type, extra_path):
    try:
        clean_path = extra_path.replace('.json', '')
        parts = clean_path.split('/')
        raw_id = parts[0]
        
        params = {
            "api_key": API_KEY,
            "languages": "ar",
            "type": "movie" if type == "movie" else "tv"
        }

        if ':' in raw_id:
            id_parts = raw_id.split(':')
            main_id = id_parts[0]
            params["season_number"] = id_parts[1]
            params["episode_number"] = id_parts[2]
        else:
            main_id = raw_id

        # La doc montre que l'API accepte le 'tt', on le laisse par défaut
        params["imdb_id"] = main_id

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }

        response = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
        
        # Si la limite est atteinte (429), on affiche un message d'avertissement dans Stremio
        if response.status_code == 429:
            return jsonify({
                "subtitles": [{
                    "id": "subdl_limit",
                    "url": "https://localhost/limit.srt",
                    "lang": "ara",
                    "name": "⚠️ SubDL API: Daily Limit Reached (Quota épuisé)"
                }]
            })

        if response.status_code != 200:
            return jsonify({"subtitles": []})
            
        data = response.json()

        if not data.get("status") or "subtitles" not in data:
            return jsonify({"subtitles": []})

        subtitles_stremio = []

        for sub in data["subtitles"]:
            sub_url_path = sub.get("url")
            if sub_url_path:
                if not sub_url_path.startswith('/subtitle/'):
                    sub_url_path = f"/subtitle/{sub_url_path.lstrip('/')}"
                
                download_url = f"https://dl.subdl.com{sub_url_path}"
                file_name = sub.get("release_name") or sub.get("name") or "Arabic Subtitle"
                
                subtitles_stremio.append({
                    "id": f"subdl_{sub.get('id', 'file')}",
                    "url": f"{HF_PUBLIC_URL}/unzip?url={download_url}",
                    "lang": "ara",
                    "name": f"🇸🇦 {file_name[:50]}"
                })

        return jsonify({"subtitles": subtitles_stremio})

    except Exception as e:
        print(f"Erreur: {e}")
        return jsonify({"subtitles": []})

@app.route('/unzip')
def unzip_subtitle():
    try:
        zip_url = request.args.get('url')
        if not zip_url:
            return "URL manquante", 400
        
        response = requests.get(zip_url, timeout=15)
        if response.status_code != 200:
            return "Fichier non trouvé", 404
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            for file_name in z.namelist():
                if "__MACOSX" in file_name:
                    continue
                if file_name.lower().endswith(('.srt', '.vtt')):
                    return send_file(
                        io.BytesIO(z.read(file_name)),
                        mimetype='text/plain; charset=utf-8' if file_name.lower().endswith('.srt') else 'text/vtt; charset=utf-8',
                        as_attachment=False,
                        download_name=file_name
                    )
        return "Aucun sous-titre trouvé", 404
    except Exception as e:
        return "Erreur décompression", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    app.run(host='0.0.0.0', port=port)
