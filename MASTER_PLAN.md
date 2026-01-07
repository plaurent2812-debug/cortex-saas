# Master Plan - NHL SaaS Application

Ce document décrit le plan complet pour le projet **NHL PREDICTOR SAAS**.
Architecture : Monolithe Modulaire (Python/Django).

Le plan est découpé en **4 Sprints** (20 Jours).

---

## SPRINT 1 : Fondations & Historique (J1-5)

**Objectif** : Socle technique solide & Base de données.

### Tâches :
- [x] Initialiser le projet 'nhl-saas' (Django 5, PostgreSQL/Supabase).
- [x] Auth : django-allauth, CustomUser.
- [ ] Migration Historique : Importer les CSV existants dans PostgreSQL.
- [ ] Nettoyage Modèles : Unifier tout sous `nhl` app.

---

## SPRINT 2 : Moteur & Dashboard (J6-10)

**Objectif** : Cerveau Logiciel & Expérience Utilisateur.

### Tâches :
- **Moteur de Calcul (Python)** :
  - Migrer la logique JS `estimate_realistic_odds` vers Python.
  - Importer les stats des gardiens/équipes via API.
- **Dashboard HTMX** :
  - Créer une interface réactive (sans rechargement de page).
  - Filtres : Conférence, Team, Position.
  - Badges : Afficher clairement "Valué" ou "Risqué".

---

## SPRINT 3 : Agents IA "Watchdog" & "Journalist" (J11-15)

**Objectif** : Automatisation intelligente & SEO.

### Tâches :
- **Agent Watchdog** :
  - Script de veille blessures (Scraping/API).
  - Déclenche un recalcul des algos si un joueur clé est out.
- **Agent Journalist** :
  - Génère automatiquement des articles/blurbs SEO pour les gros matchs.
  - "Chicago vs Detroit : Pourquoi Kane est sous-coté ce soir".
- **Notifications** : Alertes Email/Telegram pour les utilisateurs.

---

## SPRINT 4 : Paiement & Lancement (J16-20)

**Objectif** : Monétisation & Production.

### Tâches :
- **Stripe** :
  - Intégration complète (Abonnement Mensuel/Annuel).
  - Portail client.
- **Bankroll Tracking** :
  - Permettre à l'utilisateur de suivre ses gains/pertes via l'app.
- **Déploiement** :
  - Hébergement final sur **Render** ou **Railway**.
  - DNS Config.

---

## Notes
- **Hosting** : Abandon de Cloud Run pour Render/Railway (plus simple pour monorepo standard).
- **IA** : Usage intensif de Claude 3.5 Sonnet pour coder les Agents.
