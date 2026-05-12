import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
API_KEY = "xF1Vsj1tXWPxG7PP59vS1sypy_N_ETxZ"
BASE_URL = "https://api.subdl.com/api/v1"

# Le manifeste indique à Stremio ce que fait l'addon
MANIFEST = {
    "id": "com.adlen.arabic.subtitles",
    "version": "1.0.3",
    "name": "DZ-Arabic",
    "description": "Arabic Subtitles By Superadlen - Dz Devloper",
    "logo": "https://i.imgur.com/o1hZxni.png",
    "types": ["movie", "series"],
    "catalogs": [],
    "resources": ["subtitles"],
    "idPrefixes": ["tt", "tmdb"]
}

# --- ROUTES DE L'ADDON ---

@app.route('/')
def root():
    """Route racine, simple confirmation que l'addon tourne."""
    return "Addon Sous-titres Arabes OK ! By Superadlen 💯"

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
        for sub in data["subtitles"]:
            lang = sub.get("lang", "").lower()
            if lang == "arabic":
                download_url = sub.get("download_link")
                if not download_url and sub.get("url"):
                    download_url = f"https://dl.subdl.com{sub['url']}"

                if download_url:
                    # Utiliser exactement le "name" de l'API SubDL comme nom affiché
                    file_name = sub.get("name", "Sous-titre arabe")
                    
                    subtitle_entry = {
                        "id": f"subdl_{sub.get('sd_id', '')}",
                        "url": download_url,
                        "lang": "ara",
                        "name": file_name  # Affiche exactement le name de SubDL
                    }
                    
                    subtitles_stremio.append(subtitle_entry)

        return jsonify({"subtitles": subtitles_stremio})

    except Exception as e:
        print(f"Erreur: {e}")
        return jsonify({"subtitles": []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
