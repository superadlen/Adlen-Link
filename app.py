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
    "version": "1.0.0",
    "name": "Sous-titres Arabes (Adlen)",
    "description": "Fournisseur de sous-titres arabes utilisant l'API SubDL",
    "types": ["movie", "series"],
    "catalogs": [],
    "resources": ["subtitles"],
    "idPrefixes": ["tt", "tmdb"]
}

# --- ROUTES DE L'ADDON ---

@app.route('/')
def root():
    """Route racine, simple confirmation que l'addon tourne."""
    return "Addon Sous-titres Arabes OK !"

@app.route('/favicon.ico')
def favicon():
    """Évite l'erreur 404 pour favicon.ico"""
    return "", 204

@app.route('/manifest.json')
def get_manifest():
    """Stremio appelle cette route pour connaître les capacités de l'addon."""
    return jsonify(MANIFEST)

# Route modifiée pour accepter les paramètres supplémentaires de Stremio
@app.route('/subtitles/<type>/<path:extra_path>')
def get_subtitles(type, extra_path):
    """
    Route principale appelée par Stremio pour récupérer les sous-titres.
    - type : 'movie' ou 'series'
    - extra_path : l'ID et les paramètres supplémentaires (ex: tt16431404/filename=-1%3F&videoSize=...)
    """
    try:
        # Extraire l'ID de l'URL (première partie avant le "/")
        parts = extra_path.split('/')
        id = parts[0]
        
        print(f"[DEBUG] Type: {type}, ID: {id}")
        
        # Étape 1 : Préparer la requête pour l'API SubDL
        is_imdb = id.startswith('tt')
        params = {
            "api_key": API_KEY,
            "languages": "AR",  # On ne demande QUE l'arabe
            "type": "movie" if type == 'movie' else "tv"
        }
        if is_imdb:
            params["imdb_id"] = id
        else:
            params["tmdb_id"] = id

        print(f"[DEBUG] Paramètres API: {params}")

        # Étape 2 : Appeler l'API SubDL
        response = requests.get(f"{BASE_URL}/subtitles", params=params, timeout=10)
        print(f"[DEBUG] Statut API: {response.status_code}")
        
        if response.status_code != 200:
            return jsonify({"subtitles": []})
            
        data = response.json()

        # Étape 3 : Vérifier que la réponse est valide et contient des sous-titres
        if not data.get("status") or "subtitles" not in data:
            print("[DEBUG] Pas de sous-titres trouvés")
            return jsonify({"subtitles": []})

        # Étape 4 : Formater les sous-titres pour Stremio
        subtitles_stremio = []
        for sub in data["subtitles"]:
            lang = sub.get("lang", "").lower()
            # Double vérification que la langue est bien l'arabe
            if lang == "arabic":
                # Récupérer le lien de téléchargement direct
                download_url = sub.get("download_link")
                if not download_url and sub.get("url"):
                    download_url = f"https://dl.subdl.com{sub['url']}"

                if download_url:
                    # Construire l'objet sous-titre au format attendu par Stremio
                    subtitle_entry = {
                        "id": f"subdl_{sub.get('sd_id', '')}",
                        "url": download_url,
                        "lang": "ara"  # 'ara' est le code ISO 639-2 pour l'arabe
                    }
                    # Ajouter un nom descriptif si disponible
                    if sub.get("release_name"):
                        subtitle_entry["name"] = sub["release_name"]
                    subtitles_stremio.append(subtitle_entry)

        print(f"[DEBUG] Sous-titres arabes trouvés: {len(subtitles_stremio)}")
        
        # Étape 5 : Renvoyer la liste formatée à Stremio
        return jsonify({"subtitles": subtitles_stremio})

    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] API SubDL: {e}")
        return jsonify({"subtitles": []})
    except Exception as e:
        print(f"[ERREUR] Inattendue: {e}")
        return jsonify({"subtitles": []})

# --- DÉMARRAGE DU SERVEUR ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
