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

HF_PUBLIC_URL = "https://superadlen-dz-arabic.hf.space"

MANIFEST = {
    "id": "com.adlen.arabic.subtitles",
    "version": "1.9.0-debug",
    "name": "DZ-Arabic (Super-Debug)",
    "description": "Analyse de la réponse SubDL",
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

        # On prépare deux variantes pour le débug
        id_avec_tt = main_id if main_id.startswith('tt') else f"tt{main_id}"
        id_sans_tt = main_id.replace('tt', '')

        # ---- TEST 1 : Avec le "tt" ----
        params["imdb_id"] = id_avec_tt
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        res1 = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
        json1 = {}
        try: json1 = res1.json()
        except: json1 = {"text_error": res1.text}

        # ---- TEST 2 : Sans le "tt" ----
        params["imdb_id"] = id_sans_tt
        res2 = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
        json2 = {}
        try: json2 = res2.json()
        except: json2 = {"text_error": res2.text}

        # On renvoie tout à l'écran pour comprendre
        return jsonify({
            "INFO_REQUETE": {
                "id_recu_de_stremio": raw_id,
                "type_detecte": type,
                "url_api_attaquee": BASE_URL
            },
            "TEST_1_AVEC_TT": {
                "imdb_id_envoye": id_avec_tt,
                "http_status": res1.status_code,
                "reponse_subdl": json1
            },
            "TEST_2_SANS_TT": {
                "imdb_id_envoye": id_sans_tt,
                "http_status": res2.status_code,
                "reponse_subdl": json2
            }
        })

    except Exception as e:
        return jsonify({"erreur_crash_code": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    app.run(host='0.0.0.0', port=port)
