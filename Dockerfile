# Utiliser une image Python officielle légère (Slim)
# La version doit être compatible avec les requirements (Django < 5.0 => Python 3.9+)
FROM python:3.11-slim as builder

# Définir le répertoire de travail
WORKDIR /app

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installer les dépendances système nécessaires pour psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier le fichier requirements
COPY requirements.txt .

# Créer wheel pour les dépendances
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# --- Stage final ---
FROM python:3.11-slim

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Installer les dépendances d'exécution (libpq pour postgres)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copier les wheels depuis le builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Installer les dépendances python
RUN pip install --no-cache /wheels/*

# Copier le code du projet
COPY . .

# Collecter les fichiers statiques
# Note: On utilise une dummy secret key pour cette étape car les env vars ne sont pas dispos au build time
RUN SECRET_KEY=dummy_secret_key python manage.py collectstatic --noinput

# Changer propriétaire des fichiers
RUN chown -R appuser:appuser /app

# Passer à l'utilisateur non-root
USER appuser

# Exposer le port que Gunicorn utilisera (par défaut 8080 pour Cloud Run)
EXPOSE 8080

# Commande de lancement avec Gunicorn
CMD ["gunicorn", "--config", "gunicorn_config.py", "config.wsgi:application"]
