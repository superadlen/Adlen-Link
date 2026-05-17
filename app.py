import os
import requests
import zipfile
import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = "xF1Vsj1tXWPxG7PP59vS1sypy_N_ETxZ"
BASE_URL = "https://api.subdl.com/api/v1"

MANIFEST = {
    "id": "com.adlen.arabic.subtitles",
    "version": "1.2.0",
    "name": "DZ-Arabic",
    "description": "Arabic Subtitles By Superadlen - Dz Devloper  ترجمة عربية للكل",
    "logo": "https://i.imgur.com/o1hZxni.png",
    "types": ["movie", "series"],
    "catalogs": [],
    "resources": ["subtitles"],
    "idPrefixes": ["tt", "tmdb"],
    "stremioAddonsConfig": {
        "issuer": "https://stremio-addons.net",
        "signature": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMTI4Q0JDLUhTMjU2In0..EIQh4ec7V5HYJ6okcbYLeQ.9RbqBhm-uB_QMS3HZkbWvfhyaIXTldkO0NPWxtQ3Ri4QI3GptJMeoM2j8SofX4kIqF23xlBb6ZsfshAuuzkoBipHnYJy3m2O1TxEsJzTPmjDtkjvdkNMUiUDZMOJWcv0.4ecV2XmLO8uCXdx6QpkDOg"
    }
}

@app.route('/')
def root():
    return jsonify(MANIFEST)  # Renvoyer le manifest sur la racine pour le ping de Hugging Face

@app.route('/favicon.ico')
def favicon():
    return "", 204

@app.route('/manifest.json')
def get_manifest():
    return jsonify(MANIFEST)

@app.route('/subtitles/<type>/<path:extra_path>')
def get_subtitles(type, extra_path):
    try:
        parts = extra_path.split('/')
        id = parts[0]
        
        is_imdb = id.startswith('tt')
        params = {
            "api_key": API_KEY,
            "languages": "AR",
            "type": "movie" if type == 'movie' else "tv"
        }
        if is_imdb:
            params["imdb_id"] = id
        else:
            params["tmdb_id"] = id

        response = requests.get(f"{BASE_URL}/subtitles", params=params, timeout=10)
        
        if response.status_code != 200:
            return jsonify({"subtitles": []})
            
        data = response.json()

        if not data.get("status") or "subtitles" not in data:
            return jsonify({"subtitles": []})

        subtitles_stremio = []
        
        # Détection automatique de l'URL du serveur actuel (Hugging Face)
        current_host = request.host_url.rstrip('/')

        for sub in data["subtitles"]:
            lang = sub.get("lang", "").lower()
            
            # Accepte 'arabic', 'ar' ou si le filtre API a déjà bien fait son travail
            if lang == "arabic" or lang == "ar" or lang == "":
                download_url = sub.get("download_link")
                if not download_url and sub.get("url"):
                    download_url = f"https://dl.subdl.com{sub['url']}"

                if download_url:
                    file_name = sub.get("name", "")
                    
                    # Utilisation de l'URL dynamique Hugging Face
                    subtitle_entry = {
                        "id": file_name,
                        "url": f"{current_host}/unzip?url={download_url}",
                        "lang": "ara",  # Stremio a besoin de "ara" en 3 lettres pour afficher l'icône arabe
                        "name": file_name
                    }
                    
                    subtitles_stremio.append(subtitle_entry)
                    
                    subtitles_stremio.append(subtitle_entry)

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
                if file_name.lower().endswith(('.srt', '.vtt')):
                    subtitle_content = z.read(file_name)
                    
                    if file_name.lower().endswith('.srt'):
                        mimetype = 'text/plain; charset=utf-8'
                    else:
                        mimetype = 'text/vtt; charset=utf-8'
                    
                    return send_file(
                        io.BytesIO(subtitle_content),
                        mimetype=mimetype,
                        as_attachment=False,
                        download_name=file_name
                    )
        
        return "Aucun fichier .srt ou .vtt trouvé dans le zip", 404
        
    except Exception as e:
        print(f"Erreur décompression: {e}")
        return "Erreur lors de la décompression", 500

if __name__ == '__main__':
    # Force le port 7860 pour Hugging Face
    port = int(os.environ.get('PORT', 7860))
    app.run(host='0.0.0.0', port=port)
