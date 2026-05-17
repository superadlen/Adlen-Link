import os
import requests
import zipfile
import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 🔑 AJOUTE TES DIFFÉRENTES CLÉS API ICI (SÉPARÉES PAR DES VIRGULES)
API_KEYS = [
    "subdl_c2z3DxYbpqxrwMi9tqoOOvqxpKr7S9ckybH6gt5Gi1s",
    "subdl_hEkakvhQEPSxRkJYCpVALev5pH1oDpz2Lbuhrng15gQ",# Ta clé actuelle (index 0)
    "subdl_UIB1ErnZQxp_fZ925ywG4jBQiZpckH6NFN5BAU2vK2g",            # Remplace par ta 2ème clé
    "subdl_KPfvWm1nPXSjz4gkA_ATA2eYAIWasaMeBTxnUy-vWOg",            # Remplace par ta 3ème clé
    "subdl_k0f0U48XZMJN7r2E5IBEykvSoDbZG9Eu_g8ux2eDswg",            # Remplace par ta 4ème clé
    "subdl_fK8Mic862fwE5PJQwYDbx1859FewdtihJyvVtRVgVbo"             # Remplace par ta 5ème clé
]

BASE_URL = "https://api.subdl.com/api/v1/subtitles"
HF_PUBLIC_URL = "https://superadlen-dz-arabic.hf.space"

MANIFEST = {
    "id": "com.adlen.arabic.subtitles",
    "version": "2.1.0",
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
        
        # Préparation des paramètres de base (sans la clé pour le moment)
        base_params = {
            "languages": "ar",
            "type": "movie" if type == "movie" else "tv"
        }

        if ':' in raw_id:
            id_parts = raw_id.split(':')
            main_id = id_parts[0]
            base_params["season_number"] = id_parts[1]
            base_params["episode_number"] = id_parts[2]
        else:
            main_id = raw_id

        base_params["imdb_id"] = main_id

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }

        response = None
        all_limit_reached = True
        
        # 🔄 BOUCLE SUR LES CLÉS API : On les teste une par une
        for current_key in API_KEYS:
            # On fait une copie des paramètres et on injecte la clé en cours
            query_params = base_params.copy()
            query_params["api_key"] = current_key

            print(f"[DZ-Addon] Tentative avec la clé : {current_key[:8]}...")
            
            try:
                response = requests.get(BASE_URL, params=query_params, headers=headers, timeout=8)
                
                # Si la clé renvoie 429, on ignore et on passe directement à la clé suivante dans la boucle
                if response.status_code == 429:
                    print(f"[DZ-Addon] Clé {current_key[:8]}... épuisée (429). Passage à la suivante.")
                    continue
                
                # Si on a un code 200 (ou autre chose que 429), on a trouvé une clé valide ! On arrête la boucle.
                all_limit_reached = False
                break
                
            except Exception as e:
                print(f"[DZ-Addon] Erreur de connexion avec la clé {current_key[:8]}... : {e}")
                continue

        # 🚨 Si la boucle s'est finie et que toutes les clés ont renvoyé 429
        if all_limit_reached:
            return jsonify({
                "subtitles": [{
                    "id": "subdl_limit_all",
                    "url": "https://localhost/limit.srt",
                    "lang": "ara",
                    "name": "⚠️ DZ-Arabic: Toutes les clés API sont épuisées pour aujourd'hui !"
                }]
            })

        # Sécurité si aucune réponse n'a pu être obtenue du tout
        if response is None or response.status_code != 200:
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
        print(f"Erreur globale addon: {e}")
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
