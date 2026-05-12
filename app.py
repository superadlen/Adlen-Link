import os
import requests
import zipfile
import io
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
API_KEY = "xF1Vsj1tXWPxG7PP59vS1sypy_N_ETxZ"
BASE_URL = "https://api.subdl.com/api/v1"

# Le manifeste indique à Stremio ce que fait l'addon
MANIFEST = {
    "id": "com.adlen.arabic.subtitles",
    "version": "1.0.8",
    "name": "DZ-Arabic",
    "description": "Arabic Subtitles By Superadlen - Dz Devloper  ترجمة عربية للكل",
    "logo": "https://i.imgur.com/o1hZxni.png",
    "types": ["movie", "series"],
    "catalogs": [],
    "resources": ["subtitles"],
    "idPrefixes": ["tt", "tmdb"]
}

subtitle_cache = {}
# --- ROUTES DE L'ADDON ---

@app.route('/')
def root():
    """Route racine, simple confirmation que l'addon tourne."""
    return "Addon Sous-titres Arabes OK ! By Superadlen 💯تمتع يا عربي"

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

        print(f"[LOG] Recherche sous-titres pour: {id}")

        response = requests.get(f"{BASE_URL}/subtitles", params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"[LOG] API erreur: {response.status_code}")
            return jsonify({"subtitles": []})
            
        data = response.json()

        if not data.get("status") or "subtitles" not in data:
            print("[LOG] Aucun résultat de l'API")
            return jsonify({"subtitles": []})

        subtitles_stremio = []
        count = 0
        
        for sub in data["subtitles"]:
            lang = sub.get("lang", "").lower()
            if lang == "arabic":
                download_url = sub.get("download_link")
                if not download_url and sub.get("url"):
                    download_url = f"https://dl.subdl.com{sub['url']}"

                if download_url:
                    count += 1
                    file_name = sub.get("name", "subtitle").replace('.zip', '.srt')
                    subtitle_id = f"arabic_{count}"
                    
                    # Stocker l'URL pour plus tard
                    subtitle_cache[subtitle_id] = download_url
                    
                    subtitle_entry = {
                        "id": subtitle_id,
                        "url": f"{RENDER_URL}/sub/{subtitle_id}",
                        "lang": "ara",
                        "name": file_name
                    }
                    
                    subtitles_stremio.append(subtitle_entry)

        print(f"[LOG] Sous-titres arabes trouvés: {count}")
        return jsonify({"subtitles": subtitles_stremio})

    except Exception as e:
        print(f"[ERREUR] {e}")
        return jsonify({"subtitles": []})

@app.route('/sub/<subtitle_id>')
def serve_subtitle(subtitle_id):
    """
    Récupère le sous-titre depuis le cache, télécharge le zip, décompresse et renvoie le SRT
    """
    try:
        # Récupérer l'URL du cache
        download_url = subtitle_cache.get(subtitle_id)
        if not download_url:
            return "Sous-titre non trouvé", 404
        
        print(f"[LOG] Téléchargement: {download_url}")
        
        # Télécharger le zip depuis SubDL
        response = requests.get(download_url, timeout=20, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            print(f"[LOG] Échec téléchargement: {response.status_code}")
            return "Échec téléchargement", 404
        
        # Décompresser le zip
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            file_list = z.namelist()
            print(f"[LOG] Fichiers dans le zip: {file_list}")
            
            for file_name in file_list:
                if file_name.lower().endswith(('.srt', '.vtt', '.ass', '.ssa')):
                    subtitle_content = z.read(file_name)
                    
                    print(f"[LOG] Fichier extrait: {file_name}")
                    
                    return Response(
                        subtitle_content,
                        mimetype='text/plain; charset=utf-8',
                        headers={
                            'Content-Type': 'text/plain; charset=utf-8',
                            'Access-Control-Allow-Origin': '*',
                            'Cache-Control': 'no-cache'
                        }
                    )
        
        print("[LOG] Aucun fichier de sous-titre trouvé dans le zip")
        return "Pas de sous-titre dans le zip", 404
        
    except Exception as e:
        print(f"[ERREUR] {e}")
        return f"Erreur: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
