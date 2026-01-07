# Guide de Déploiement CORTEX - Prochaines Étapes

Ce guide détaille les 3 étapes post-transformation pour finaliser CORTEX.

---

## 🧪 Étape 1 : Test Local

### Vérifier que le serveur tourne

```bash
# Si pas encore lancé :
cd /Users/pierrelaurent/Desktop/nhl-saas
source venv/bin/activate  # Activer l'environnement virtuel
python3 manage.py runserver
```

**Note** : Le serveur semble déjà actif ! 

### Tests à effectuer

1. **Landing Page** : http://localhost:8000/
   - ✅ Le ticker doit défiler avec les résultats
   - ✅ Le graphique Performance vs Public doit s'afficher
   - ✅ Les 3 cartes features doivent être visibles
   - ✅ CTAs "🎁 Voir mes 3 Pronos Gratuits" fonctionnels

2. **Dashboard NHL** : http://localhost:8000/nhl/dashboard/
   - ✅ Filtres par équipe fonctionnels (HTMX)
   - ✅ Si utilisateur gratuit : "CORTEX Bankers" vide
   - ✅ Si utilisateur premium : "CORTEX Bankers" rempli

3. **Test Sécurité Freemium**
   ```bash
   # Dans un nouveau terminal
   python3 manage.py shell
   ```
   
   ```python
   from users.models import CustomUser
   
   # Créer un user gratuit de test
   user = CustomUser.objects.create_user(
       email='test.free@cortex.com',
       password='testpass123'
   )
   print(f"User créé : {user.email}, Premium: {user.is_premium}")
   # Devrait afficher : Premium: False
   exit()
   ```
   
   Puis se connecter sur http://localhost:8000/accounts/login/ avec :
   - Email: `test.free@cortex.com`
   - Password: `testpass123`
   
   → Vérifier que le dashboard ne montre PAS les "CORTEX Bankers"

4. **Test Score CORTEX**
   ```bash
   python3 manage.py shell
   ```
   
   ```python
   from nhl.models import GameStats
   
   # Récupérer un exemple
   game = GameStats.objects.filter(
       algo_score_goal__isnull=False,
       python_prob__isnull=False
   ).first()
   
   if game:
       print(f"Joueur: {game.name}")
       print(f"Algo Score: {game.algo_score_goal}")
       print(f"Python Prob: {game.python_prob}")
       print(f"CORTEX Score: {game.cortex_score}")
       print(f"Formule vérifiée: {(game.algo_score_goal * 0.6) + (game.python_prob * 0.4)}")
   else:
       print("Aucune donnée dans data_lake. Lancer fetch_nhl_data d'abord.")
   exit()
   ```

5. **Test Injury Guardian**
   ```bash
   python3 manage.py injury_guardian
   ```
   
   Devrait afficher :
   ```
   [Injury Guardian] Starting injury check...
     Checking EDM...
     Checking TOR...
     ...
   [Injury Guardian] Complete! Checked X teams, marked Y predictions as injured.
   ```

---

## 📊 Étape 2 : Exécuter schema_performance_log.sql dans Supabase

### Option A : Via Supabase Dashboard (Recommandé)

1. **Se connecter à Supabase**
   - Aller sur https://supabase.com
   - Se connecter à votre projet

2. **Accéder au SQL Editor**
   - Dans le menu latéral gauche : cliquer sur "SQL Editor"
   - Cliquer sur "+ New query"

3. **Copier le Schema SQL**
   ```bash
   # Dans votre terminal local
   cat /Users/pierrelaurent/Desktop/nhl-saas/schema_performance_log.sql
   ```
   
   Ou ouvrir le fichier dans votre éditeur et copier tout le contenu.

4. **Exécuter dans Supabase**
   - Coller le contenu dans l'éditeur SQL de Supabase
   - Cliquer sur "Run" (ou Ctrl+Enter)
   - Vérifier qu'il n'y a pas d'erreurs

5. **Vérification**
   - Dans le menu latéral : "Table Editor"
   - Chercher la table `performance_log`
   - Elle devrait apparaître avec toutes les colonnes

### Option B : Via psql (Ligne de commande)

```bash
# Récupérer votre DATABASE_URL depuis .env
cat .env | grep DATABASE_URL

# Se connecter avec psql
psql "votre_database_url_ici"

# Dans psql :
\i /Users/pierrelaurent/Desktop/nhl-saas/schema_performance_log.sql

# Vérifier
\dt performance_log
\d performance_log

# Quitter
\q
```

### Vérifier que tout fonctionne

Dans Supabase SQL Editor, exécuter :
```sql
-- Vérifier que la table existe
SELECT COUNT(*) FROM performance_log;

-- Devrait retourner : 0 (table vide mais créée)

-- Vérifier les vues
SELECT * FROM v_cortex_performance;

-- Test d'insertion
INSERT INTO performance_log 
    (date, player_name, team, prediction_type, 
     predicted_odds, cortex_score, actual_result, stake, profit)
VALUES
    ('2026-01-07', 'Test Player', 'EDM', 'GOAL', 
     2.50, 120.5, TRUE, 1.0, 1.50);

-- Vérifier
SELECT * FROM performance_log;

-- Nettoyer le test
DELETE FROM performance_log WHERE player_name = 'Test Player';
```

---

## ⏰ Étape 3 : Configurer CRON pour Injury Guardian

### Option A : CRON macOS (Production locale)

1. **Éditer le crontab**
   ```bash
   crontab -e
   ```

2. **Ajouter cette ligne** (adapter le chemin)
   ```bash
   # Injury Guardian - Surveillance blessures NHL (toutes les 30min)
   */30 * * * * cd /Users/pierrelaurent/Desktop/nhl-saas && /Users/pierrelaurent/Desktop/nhl-saas/venv/bin/python3 manage.py injury_guardian >> /tmp/injury_guardian.log 2>&1
   ```

3. **Sauvegarder et quitter**
   - Dans vim : Appuyer sur `Esc`, puis `:wq` puis `Enter`
   - Dans nano : `Ctrl+X`, puis `Y`, puis `Enter`

4. **Vérifier le CRON**
   ```bash
   crontab -l
   ```

5. **Tester que ça fonctionne** (attendre 30min ou forcer)
   ```bash
   # Voir les logs
   tail -f /tmp/injury_guardian.log
   
   # Forcer une exécution manuelle pour tester
   cd /Users/pierrelaurent/Desktop/nhl-saas
   source venv/bin/activate
   python3 manage.py injury_guardian
   ```

### Option B : Render/Railway (Production cloud)

Si vous déployez sur Render ou Railway :

**Render** :
1. Dashboard → Votre service → "Cron Jobs"
2. Ajouter :
   - Name: `injury_guardian`
   - Schedule: `*/30 * * * *`
   - Command: `python manage.py injury_guardian`

**Railway** :
1. Settings → Cron Jobs
2. Ajouter :
   - `*/30 * * * * python manage.py injury_guardian`

**Heroku** :
Utiliser Heroku Scheduler addon :
```bash
heroku addons:create scheduler:standard
heroku addons:open scheduler
```
Puis ajouter : `python manage.py injury_guardian` (toutes les 30min)

### Option C : Celery Beat (Pour futures évolutions)

Si vous voulez un système plus robuste plus tard :

```python
# Dans settings.py
CELERY_BEAT_SCHEDULE = {
    'injury-guardian': {
        'task': 'nhl.tasks.check_injuries',
        'schedule': crontab(minute='*/30'),
    },
}
```

Mais pour l'instant, CRON simple suffit !

---

## ✅ Checklist de Validation Finale

Une fois les 3 étapes complétées :

- [ ] **Test Local** : Landing page affiche ticker + graphique
- [ ] **Test Sécurité** : User gratuit ne voit PAS les CORTEX Bankers
- [ ] **Test Score** : `game.cortex_score` retourne la bonne valeur
- [ ] **Test Injury** : `manage.py injury_guardian` s'exécute sans erreur
- [ ] **Supabase** : Table `performance_log` existe et est accessible
- [ ] **CRON** : `crontab -l` montre bien la tâche injury_guardian
- [ ] **Logs** : `/tmp/injury_guardian.log` se remplit toutes les 30min

---

## 🚀 Une fois validé

Vous pourrez :

1. **Alimenter performance_log** 
   - Créer un script qui compare pronos vs résultats réels
   - Remplacer les données mockées du graphique par les vraies

2. **Monitoring**
   - Sentry pour erreurs
   - Slack webhook pour alertes

3. **Déploiement Production**
   - Render / Railway / Heroku
   - DNS personnalisé
   - SSL/HTTPS automatique

---

## 🆘 Troubleshooting

### Problème : "Port already in use"
```bash
# Trouver le processus
lsof -i :8000
# Tuer le processus
kill -9 <PID>
```

### Problème : "ModuleNotFoundError"
```bash
# Réactiver le venv
source venv/bin/activate
pip install -r requirements.txt
```

### Problème : "CRON ne s'exécute pas"
```bash
# Vérifier les logs système macOS
tail -f /var/log/system.log | grep CRON

# Tester manuellement le chemin complet
/Users/pierrelaurent/Desktop/nhl-saas/venv/bin/python3 /Users/pierrelaurent/Desktop/nhl-saas/manage.py injury_guardian
```

### Problème : "Table already exists" dans Supabase
```sql
-- Supprimer et recréer
DROP TABLE IF EXISTS performance_log CASCADE;
-- Puis ré-exécuter schema_performance_log.sql
```

---

## 📞 Besoin d'aide ?

Si un problème persiste, partage-moi :
1. La commande exacte exécutée
2. Le message d'erreur complet
3. Le contexte (local / production)

Bon déploiement ! 🎯
