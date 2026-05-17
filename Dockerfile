FROM python:3.10-slim

WORKDIR /app

# Copie des fichiers de dépendances
COPY requirements.txt ./

# Installation des paquets Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code de l'addon
COPY . .

# Exposition du port obligatoire de Hugging Face
EXPOSE 7860

# Lancement de l'application avec Gunicorn sur le port 7860
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "60"]
