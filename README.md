# Jarvis NHL SaaS

Application de prédiction et d'analyse de paris sportifs NHL, propulsée par l'IA.

## Architecture

- **Backend** : Django 5.x (Python)
- **Database** : PostgreSQL (Supabase)
- **Authentification** : Django Allauth (Email login)
- **Frontend** : Django Templates + TailwindCSS
- **Déploiement** : Docker + Google Cloud Run
- **Paiements** : Stripe

## Structure du Projet

- `config/` : Configuration globale Django
- `core/` : Logique métier (Modèles, Vues, Services)
- `users/` : Gestion des utilisateurs personnalisée (Custom User)
- `templates/` : Templates globaux (base, index)

## Installation Locale

1. **Cloner le projet**
   ```bash
   git clone <repo_url>
   cd nhl-saas
   ```

2. **Environnement Virtuel**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Variables d'environnement**
   Copier `.env.example` vers `.env.` et remplir les valeurs
   ```bash
   cp .env.example .env.
   ```

5. **Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Lancer le serveur**
   ```bash
   python manage.py runserver
   ```
   Accéder à http://127.0.0.1:8000

## Commandes Utiles

- Créer un superuser : `python manage.py createsuperuser`
- Mises à jour des modèles : `python manage.py makemigrations`
- Collecter les fichiers statiques : `python manage.py collectstatic`

## Déploiement

Voir [DEPLOYMENT.md](DEPLOYMENT.md) pour les instructions complètes de déploiement sur Cloud Run.
# Railway deployment
