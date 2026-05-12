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
    "version": "1.0.6",
    "name": "DZ-Arabic",
    "description": "Arabic Subtitles By Superadlen - Dz Devloper  ترجمة عربية للكل",
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
                    file_name = sub.get("name", "").replace('.zip', '.srt')
                    
                    # Créer un ID unique avec l'URL encodée
                    subtitle_id = f"sub_{abs(hash(download_url))}"
                    
                    subtitle_entry = {
                        "id": subtitle_id,
                        "url": f"{RENDER_URL}/subtitle/{subtitle_id}.srt?url={requests.utils.quote(download_url)}",
                        "lang": "ara",
                        "name": file_name
                    }
                    
                    subtitles_stremio.append(subtitle_entry)

        return jsonify({"subtitles": subtitles_stremio})

    except Exception as e:
        print(f"Erreur: {e}")
        return jsonify({"subtitles": []})

@app.route('/subtitle/<subtitle_id>.srt')
def serve_subtitle(subtitle_id):
    """
    Télécharge et décompresse le sous-titre, puis le renvoie en .srt
    """
    try:
        zip_url = request.args.get('url')
        if not zip_url:
            return "URL manquante", 400
        
        # Télécharger le zip
        print(f"Téléchargement: {zip_url}")
        response = requests.get(zip_url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        
        if response.status_code != 200:
            print(f"Erreur téléchargement: {response.status_code}")
            return "Fichier non trouvé", 404
        
        # Décompresser
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            for file_name in z.namelist():
                if file_name.lower().endswith(('.srt', '.vtt')):
                    subtitle_content = z.read(file_name)
                    
                    # Si c'est du VTT, le convertir en SRT simple
                    if file_name.lower().endswith('.vtt'):
                        subtitle_content = subtitle_content.decode('utf-8', errors='ignore')
                        subtitle_content = subtitle_content.replace('WEBVTT\n\n', '')
                    
                    print(f"Fichier trouvé: {file_name}")
                    return Response(
                        subtitle_content,
                        mimetype='text/plain; charset=utf-8',
                        headers={
                            'Content-Disposition': 'inline',
                            'Access-Control-Allow-Origin': '*'
                        }
                    )
        
        print("Aucun fichier srt/vtt trouvé")
        return "Aucun sous-titre trouvé", 404
        
    except Exception as e:
        print(f"Erreur: {e}")
        return f"Erreur: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
