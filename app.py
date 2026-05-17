import os
import requests
import zipfile
import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 🔑 TES CLÉS API SUBDL
API_KEYS = [
    "subdl_c2z3DxYbpqxrwMi9tqoOOvqxpKr7S9ckybH6gt5Gi1s",
    "subdl_lTE8o46aAb7qssQj-kK-QwALDoBRu0_SXd6Rl8MxSrw",
    "subdl_hEkakvhQEPSxRkJYCpVALev5pH1oDpz2Lbuhrng15gQ",
    "subdl_UIB1ErnZQxp_fZ925ywG4jBQiZpckH6NFN5BAU2vK2g",
    "subdl_KPfvWm1nPXSjz4gkA_ATA2eYAIWasaMeBTxnUy-vWOg",
    "subdl_k0f0U48XZMJN7r2E5IBEykvSoDbZG9Eu_g8ux2eDswg",
    "subdl_fK8Mic862fwE5PJQwYDbx1859FewdtihJyvVtRVgVbo"
]

BASE_URL = "https://api.subdl.com/api/v1/subtitles"
HF_PUBLIC_URL = "https://superadlen-dz-arabic.hf.space"

MANIFEST = {
    "id": "com.adlen.arabic.subtitles",
    "version": "2.5.1",
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
        
        for current_key in API_KEYS:
            query_params = base_params.copy()
            query_params["api_key"] = current_key
            
            try:
                response = requests.get(BASE_URL, params=query_params, headers=headers, timeout=8)
                if response.status_code == 429:
                    continue
                all_limit_reached = False
                break
            except Exception:
                continue

        if all_limit_reached:
            return jsonify({
                "subtitles": [{
                    "id": f"{raw_id}_limit_all",
                    "url": "https://localhost/limit.srt",
                    "lang": "ara",
                    "name": "⚠️ DZ-Arabic: Toutes les clés API sont épuisées !"
                }]
            })

        if response is None or response.status_code != 200:
            return jsonify({"subtitles": []})
            
        data = response.json()

        if not data.get("status") or "subtitles" not in data:
            return jsonify({"subtitles": []})

        subtitles_stremio = []

        # Extraction du nom du film/série global trouvé par SubDL
        film_global_name = ""
        if data.get("results") and len(data["results"]) > 0:
            film_global_name = data["results"][0].get("name", "")

        for sub in data["subtitles"]:
            sub_url_path = sub.get("url")
            if sub_url_path:
                if not sub_url_path.startswith('/subtitle/'):
                    sub_url_path = f"/subtitle/{sub_url_path.lstrip('/')}"
                
                download_url = f"https://dl.subdl.com{sub_url_path}"
                
                # 1. On détermine un nom propre lisible pour l'utilisateur
                display_name = sub.get("release_name") or sub.get("name")
                
                if not display_name or ".zip" in display_name.lower():
                    if film_global_name:
                        sub_id_short = sub.get('id') or "pack"
                        display_name = f"{film_global_name} (Version {sub_id_short})"
                    else:
                        sub_id_short = sub.get('id') or "Pack"
                        display_name = f"Traduction Arabe {sub_id_short}"

                display_name = str(display_name).strip()
                
                # 2. Génération d'un identifiant technique unique
                unique_sub_id = sub.get('id') or sub.get('release_id') or hash(download_url)
                
                # 🛠️ CORRECTION STRUCTURELLE : Pour forcer Stremio à ignorer l'ID à l'affichage,
                # on utilise un formalisme strict où le champ "name" sert de label court (le drapeau)
                # et le champ "name" contient le vrai nom de la release pour écraser l'ID technique.
                subtitles_stremio.append({
                    "id": f"{raw_id}_subdl_{unique_sub_id}",
                    "url": f"{HF_PUBLIC_URL}/unzip?url={download_url}",
                    "lang": "ara",
                    "name": f"🇸🇦 {display_name[:60]}"  # Stremio affiche ce champ en priorité comme titre du sous-titre
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
