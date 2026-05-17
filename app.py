import os
import requests
import zipfile
import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = "xF1Vsj1tXWPxG7PP59vS1sypy_N_ETxZ"
BASE_URL = "https://api.subdl.com/api/v1/subtitles"

# URL publique absolue de ton Space Hugging Face
HF_PUBLIC_URL = "https://superadlen-dz-arabic.hf.space"

MANIFEST = {
    "id": "com.adlen.arabic.subtitles",
    "version": "1.8.0",
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
        
        params = {
            "api_key": API_KEY,
            "languages": "ar",  # Test en minuscules comme l'exemple JS de la doc
            "type": "movie" if type == "movie" else "tv"
        }

        if ':' in raw_id:
            id_parts = raw_id.split(':')
            main_id = id_parts[0]
            params["season_number"] = id_parts[1]
            params["episode_number"] = id_parts[2]
        else:
            main_id = raw_id

        if main_id.startswith('tt'):
            # Double sécurité : SubDL rejette souvent le 'tt' sur l'endpoint global v1
            params["imdb_id"] = main_id.replace('tt', '')
        else:
            params["tmdb_id"] = main_id

        # Camouflage : On fait croire à SubDL que la requête vient d'un ordinateur sous Windows avec Chrome
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

        response = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
        
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
                
                subtitle_entry = {
                    "id": f"subdl_{sub.get('id', 'file')}",
                    "url": f"{HF_PUBLIC_URL}/unzip?url={download_url}",
                    "lang": "ara",
                    "name": f"🇸🇦 {file_name[:50]}"
                }
                subtitles_stremio.append(subtitle_entry)

        return jsonify({"subtitles": subtitles_stremio})

    except Exception as e:
        print(f"Erreur DZ-Arabic Subtitles: {e}")
        return jsonify({"subtitles": []})

@app.route('/unzip')
def unzip_subtitle():
    try:
        zip_url = request.args.get('url')
        if not zip_url:
            return "URL manquante", 400
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(zip_url, headers=headers, timeout=15)
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
