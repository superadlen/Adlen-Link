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
    "types": ["movie", "series"],  # Fonctionne pour films et séries
    "catalogs": [],
    "resources": ["subtitles"],
    "idPrefixes": ["tt", "tmdb"]   # Accepte les IDs IMDB (tt...) et TMDB
}

# --- ROUTES DE L'ADDON ---

@app.route('/')
def root():
    """Route racine, simple confirmation que l'addon tourne."""
    return "Addon Sous-titres Arabes en cours d'exécution !"

@app.route('/manifest.json')
def get_manifest():
    """Stremio appelle cette route pour connaître les capacités de l'addon."""
    return jsonify(MANIFEST)

@app.route('/subtitles/<type>/<id>.json')
def get_subtitles(type, id):
    """
    Route principale appelée par Stremio pour récupérer les sous-titres.
    - type : 'movie' ou 'series'
    - id : identifiant IMDB (ex: tt0944947) ou TMDB
    """
    try:
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

        # Étape 2 : Appeler l'API SubDL
        response = requests.get(f"{BASE_URL}/subtitles", params=params)
        response.raise_for_status()  # Lève une erreur si le statut n'est pas 200
        data = response.json()

        # Étape 3 : Vérifier que la réponse est valide et contient des sous-titres
        if not data.get("status") or "subtitles" not in data:
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

        # Étape 5 : Renvoyer la liste formatée à Stremio
        return jsonify({"subtitles": subtitles_stremio})

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel à l'API SubDL : {e}")
        return jsonify({"subtitles": []})
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        return jsonify({"subtitles": []})

# --- DÉMARRAGE DU SERVEUR ---
if __name__ == '__main__':
    # Render fournit le port via la variable d'environnement PORT, sinon on utilise 5000 en local.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
