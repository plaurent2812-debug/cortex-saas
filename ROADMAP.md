🗺️ ROADMAP & SUIVI PROJET (CORTEX)
Ce document est la source unique de vérité pour le développement de CORTEX. Il croise les objectifs finaux (MASTER_PLAN) avec l'état réel du code (CONTEXT).

Dernière mise à jour : 06 Janvier 2026 État Global : 🚧 En cours de consolidation (Transition Prototype -> SaaS propre)

🛠️ Dette Technique & Urgences (PRIORITÉ ABSOLUE)
Ces tâches sont bloquantes. Elles doivent être résolues avant tout nouveau développement pour garantir la stabilité de l'IA.

[ ] Sécurité & Config (Audit)

[ ] Vérifier que aucune clé API (Stripe, Supabase) n'est en dur dans le code. Tout doit être dans .env.

[ ] Fixer LOGIN_REDIRECT_URL (doublon dans settings).

[ ] Aligner la version cible Django (Target: 5.2.9).

[x] Nettoyage Modèles (Architecture)

[x] Supprimer le doublon core.models.Player vs nhl.models.GameStats.

[x] Action : Unifier sous nhl.models.GameStats avec Meta: managed=False (Table Supabase Maîtresse).

[x] Nettoyage Vues & URLs

[x] Supprimer les doublons de views dashboard (core vs nhl).

[x] Centraliser toute la logique métier dans l'app nhl.

🗓️ Cycles de Développement (Sprints)
✅ SPRINT 1 : Fondations & DB (J1-5) (Terminé/En cours de consolidation)
Objectif : Base SaaS sécurisée, DB PostgreSQL & Migration Historique CSV.

[x] Setup Projet : Django 5, PostgreSQL (Supabase), Env Vars.

[x] Authentification : Login/Signup (Allauth), User Model Custom.

[x] UI Base : Navbar dynamique, TailwindCSS.

[x] Ingestion Données Brutes (Migration CSV/History).

🚧 SPRINT 2 : Moteur de calcul & Dashboard (J6-10)
Objectif : Migration du cerveau (Python) & Dashboard HTMX.

[x] Connexion Data : Lecture de la table Supabase data_lake.

[ ] Moteur de Calcul (Migration Python) :

[ ] calculate_odds() : Implémenter la bonne logique mathématique.

[ ] Dashboard HTMX :

[ ] Filtres temporels / Live refresh.

[ ] UI/UX "Pro" (Badges Value, Risk).

🔮 SPRINT 3 : Agents IA "Watchdog" & "Journalist" (J11-15)
Objectif : Intelligence automatisée & Contenu SEO.

[ ] Agent Watchdog :

[ ] API/Scraping Blessures (Rotowire/DailyFaceoff).

[ ] Trigger recalcul cotes si blessure majeure.

[ ] Agent Journalist :

[ ] Génération contenu SEO automatisé (Analyses d'avant-match).

[ ] Notifications Utililateurs.

💸 SPRINT 4 : Paiement & Lancement (J16-20)
Objectif : Monétisation (Stripe), Bankroll & Go Live.

[ ] Intégration Paiement (Stripe) :

[ ] Abonnements / Checkout / Webhooks.

[ ] Tracking Bankroll Utilisateur.

[ ] Hosting Final (Render ou Railway).

[ ] Lancement Public.

🧠 Notes & Décisions Techniques
App Structure :

users/ : Auth & User Model.

nhl/ : Coeur de l'app (Data, Algo, Dashboard).

core/ : Landing page, Webhooks, utils génériques.

Agents :
Watchdog : Processus background (Celery ou Custom Command) qui surveille les inputs externes.
Journalist : LLM Integration (OpenAI/Anthropic) pour rédiger du texte à partir des stats.

Data Flow :
python manage.py fetch_nhl (Cron) -> API NHL.
Upsert dans Supabase (data_lake).
Django Model (managed=False) lit Supabase.
View applique calculate_odds() à la volée -> Template.