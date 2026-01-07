# CONTEXT.md

## Stack & Architecture

### Stack Détectée
- **Backend** : Python 3.9+, Django 5.2.9 (Mise à jour majeure par rapport au requirements.txt qui indique <5.0)
- **Database** : PostgreSQL via Supabase (table `data_lake`)
- **Frontend** : Django Templates + TailwindCSS (CDN) + HTMX (mentionné mais pas vu explicitement utilisé)
- **Auth** : `django-allauth` (Email First)
- **Paiement** : Stripe (installé, config de base présente)
- **Déploiement** : Docker + Gunicorn + WhiteNoise

### Structure Clé
- `config/` : Configuration globale (Settings, URLS). Note : Présence de doublons dans `settings.py`.
- `users/` : Gestion des utilisateurs (`CustomUser`) avec champs Premium & Stripe.
- `nhl/` : Cœur fonctionnel (Dashboard, Modèle `GameStats`, Services).
- `core/` : App "historique" ou fourre-tout (Landing page, Paiement Stripe, Modèle `Player` dupliqué).
- `templates/` : Templates globaux (`base.html` avec Navbar).

---

## État des Fonctionnalités (Audit)

### ✅ Fini / Fonctionnel
- **Authentification** : Login/Signup via Email (`users` app + `allauth`). Modèle User prêt pour le SaaS.
- **Connexion DB** : Django arrive à lire la table `data_lake` de Supabase.
- **Dashboard UI** : Interface responsive avec distinction visuelle Public/Premium (floutage).
- **Logique Premium (Base)** : Le template vérifie `is_premium` et adapte l'affichage.

### 🚧 Placeholders / Incomplet
- **Logique Métier (`nhl/services.py`)** : La fonction `calculate_odds` contient une logique simplifiée/hardcodée ("Example logic based on request prompt").
- **Récupération de Données** : Les vues (`nhl` et `core`) font un `[:50]` brute sur la table. Aucune filtration par date (ex: matchs du jour).
- **Paiement Stripe** :
  - Vue `CreateCheckoutSessionView` présente dans `core` mais redirection pas claire depuis le dashboard `nhl`.
  - Webhook présent et semble correct (update `is_premium`).
  - Pas de portail client pour gérer l'abonnement.
- **Pipeline Data** : Pas de script de synchronisation automatique (CRON) visible pour mettre à jour Supabase depuis l'API NHL.

---

## Dette Technique & Alertes

- 🔴 **Doublons de Modèles (CRITIQUE)** :
  - `core.models.Player` (`managed=False`)
  - `nhl.models.GameStats` (`managed=True` ! DANGER - risque d'écraser la table Supabase).
  - Les deux pointent vers la même table `data_lake`. Il faut en garder un seul.
- 🔴 **Doublons de Vues/URLs** :
  - `core.views.dashboard` rendu `core/dashboard.html`
  - `nhl.views.dashboard` rendu `nhl/dashboard.html`
  - `settings.py` a deux définitions de `LOGIN_REDIRECT_URL` (lignes 96 et 202). La dernière (`/nhl/dashboard/`) gagne, mais c'est sale.
- 🟠 **Incohérence Versions** : `requirements.txt` limite Django à <5.0, mais le projet tourne en 5.2.9.
- 🟠 **Hardcoded Logic** : `nhl/services.py` utilise des valeurs fixes (0.60) qui devraient probablement être configurables.
- 🟠 **Code Mort** : `seed_nhl_data.py` à la racine semble être un script temporaire.

---

## Prochaines Étapes Logiques (MVP)

1.  **Nettoyage Architecture** :
    - Fusionner/Supprimer le doublon `core` vs `nhl`. Recommandation : Garder `core` pour le général (Home, Stripe) et `nhl` pour le métier, mais UNIFIER le modèle de données.
    - Passer le modèle `GameStats` en `managed=False` impérativement.
2.  **Fix Data Fetching** :
    - Modifier la query pour ne récupérer que les matchs du jour/futurs, pas les 50 premiers historiques.
3.  **Finaliser Stripe** :
    - Vérifier le lien du bouton "Débloquer" dans le template pour qu'il pointe vers la bonne vue de checkout.
4.  **Pipeline d'Ingestion** :
    - Créer la Management Command Django pour pomper l'API NHL et remplir Supabase (le "Cerveau" manquant).
