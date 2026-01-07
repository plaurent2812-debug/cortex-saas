# Guide de Déploiement - Jarvis NHL

Ce guide détaille les étapes pour déployer l'application sur Google Cloud Run avec une base de données Supabase.

## Pré-requis

1. Compte Google Cloud Platform (GCP)
2. Compte Supabase (PostgreSQL)
3. Stripe (si paiements actifs)
4. CLI installés : `gcloud`, `docker`

## 1. Bases de données (Supabase)

1. Créer un nouveau projet sur Supabase.
2. Récupérer l'URL de connexion (Transaction Pooler est recommandé pour serverless).
   - Format : `postgres://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`

## 2. Configuration Google Cloud

### Activer les services
```bash
gcloud services enable run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com
```

### Créer les secrets (Recommandé)
Plutôt que de passer les variables en clair, utilisez Secret Manager.
```bash
gcloud secrets create django-settings --replication-policy="automatic"
```

## 3. Déploiement sur Cloud Run

### Option A : Déploiement direct depuis le code source
Google Cloud Build va construire le conteneur automatiquement.

```bash
gcloud run deploy jarvis-nhl \
  --source . \
  --region europe-west9 \
  --allow-unauthenticated \
  --set-env-vars="DEBUG=False" \
  --set-env-vars="ALLOWED_HOSTS=jarvis-nhl-xyz.a.run.app" \
  --set-env-vars="DATABASE_URL=votre_url_supabase" \
  --set-env-vars="SECRET_KEY=votre_secret_key"
```

### Option B : Build Docker local et Push (Plus rapide pour iterer)
```bash
# 1. Build
docker build -t gcr.io/[PROJECT_ID]/jarvis-nhl .

# 2. Push
docker push gcr.io/[PROJECT_ID]/jarvis-nhl

# 3. Deploy
gcloud run deploy jarvis-nhl \
  --image gcr.io/[PROJECT_ID]/jarvis-nhl \
  --region europe-west9 \
  --allow-unauthenticated \
  --set-env-vars=...
```

## 4. Post-Déploiement

### Migrations
Il faut exécuter les migrations sur la base de données de production.
Vous pouvez le faire via un "Job" Cloud Run ou via une instance locale connectée à la DB prod.

```bash
# Depuis local (avec DATABASE_URL pointant vers prod)
python manage.py migrate
```

### Création Superuser
Idem, à faire une fois.
```bash
python manage.py createsuperuser
```

## 5. Maintenance

### Mises à jour
Pour mettre à jour l'application, relancez simplement la commande `gcloud run deploy`.

### Logs
Les logs sont disponibles dans la console Cloud Run ou via :
```bash
gcloud beta run services logs tail jarvis-nhl
```
