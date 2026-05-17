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

# URL de ton Space Hugging Face
HF_PUBLIC_URL = "https://superadlen-dz-arabic.hf.space"

MANIFEST = {
    "id": "com.adlen.arabic.subtitles",
    "version": "1.4.1-debug",
    "name": "DZ-Arabic (Debug)",
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
    return jsonify(MANIFEST)

@app.route('/favicon.ico')
def favicon():
    return "", 204

@app.route('/manifest.json')
def get_manifest():
    return jsonify(MANIFEST)

@app.route('/subtitles/<type>/<path:extra_path>')
def get_subtitles(type, extra_path):
    try:
        clean_path = extra_path.replace('.json', '')
        parts = clean_path.split('/')
        raw_id = parts[0]
        
        if ':' in raw_id:
            main_id = raw_id.split(':')[0]
        else:
            main_id = raw_id
            
        is_imdb = main_id.startswith('tt')
        
        params = {
            "api_key": API_KEY,
            "languages": "AR"
        }
        
        if is_imdb:
            params["imdb_id"] = main_id.replace('tt', '')
        else:
            params["tmdb_id"] = main_id

        endpoint = "movie" if type == "movie" else "tv"
        subdl_url = f"{BASE_URL}/subtitles/{endpoint}"

        # 1. Envoi de la requête vers l'API SubDL
        response = requests.get(subdl_url, params=params, timeout=10)
        
        # 2. Renvoi immédiat de la réponse brute pour analyse
        try:
            return jsonify({
                "DEBUG_SUBDL_STATUS_CODE": response.status_code,
                "DEBUG_SUBDL_RESPONSE": response.json()
            })
        except Exception:
            return jsonify({
                "DEBUG_SUBDL_STATUS_CODE": response.status_code,
                "DEBUG_SUBDL_TEXT": response.text
            })

    except Exception as e:
        return jsonify({"error_debug": str(e)})

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
    port = int(os.environ.get('PORT', 7860))
    app.run(host='0.0.0.0', port=port)
