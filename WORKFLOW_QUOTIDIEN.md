# CORTEX - Workflow Quotidien Automatisé

Ce document décrit le workflow quotidien de CORTEX avec les scripts automatisés.

---

## 📅 Planning CRON Quotidien

### 🕛 12h00 - Récupération Résultats
**Script** : `fetch_game_results.py`

```bash
0 12 * * * cd /Users/pierrelaurent/Desktop/nhl-saas && /path/to/venv/bin/python3 manage.py fetch_game_results >> /tmp/cortex_results.log 2>&1
```

**Rôle** :
- Récupère les **résultats réels** des matchs de la veille (17h30-4h30)
- Met à jour `result_goal` et `result_shot` dans `data_lake`
- Permet le calcul ROI et l'entraînement ML

**Exemple Output** :
```
[Fetch Results] Starting...
Checking results for 2026-01-07
  > Processing MTL @ CGY (Game 2026020123)
    ✓ Nick Suzuki: 1G, 2A, 4SOG (Predicted prob: 45%)
    ✓ Cole Caufield: 0G, 1A, 6SOG (Predicted prob: 38%)
[Fetch Results] Complete! Updated 87 players across 5 games.
```

---

### 🕓 16h00 - Préparation Matchs du Jour
**Scripts** : `fetch_nhl_data.py` + `injury_guardian.py`

```bash
# Récupération matchs + calcul pronos
0 16 * * * cd /Users/pierrelaurent/Desktop/nhl-saas && /path/to/venv/bin/python3 manage.py fetch_nhl_data >> /tmp/cortex_fetch.log 2>&1

# Vérification blessures (30min après)
30 16 * * * cd /Users/pierrelaurent/Desktop/nhl-saas && /path/to/venv/bin/python3 manage.py injury_guardian >> /tmp/cortex_injuries.log 2>&1
```

**Rôle** :
- `fetch_nhl_data` :
  - Récupère le calendrier NHL du jour depuis API
  - Analyse les rosters et stats joueurs
  - Calcule les prédictions CORTEX (python_prob, algo_score)
  - Insère dans `data_lake` (Supabase)

- `injury_guardian` :
  - Lit l'API NHL pour détecter joueurs IR/OUT
  - Marque les pronos comme `INJURED`
  - Évite les faux pronos sur joueurs absents

**Exemple Output** :
```
Starting NHL Data Ingestion...
Processing 5 games for 2026-01-08...
  > Analyzing WSH vs DAL
    -> Saved 19 players for WSH
    -> Saved 20 players for DAL
```

---

### ⏰ Surveillance Continue - Injury Guardian
**Fréquence** : Toutes les 30 minutes (17h-23h)

```bash
*/30 17-23 * * * cd /Users/pierrelaurent/Desktop/nhl-saas && /path/to/venv/bin/python3 manage.py injury_guardian >> /tmp/injury_guardian.log 2>&1
```

**Rôle** :
- Surveillance en temps quasi-réel des blessures
- Important car les annonces peuvent tomber à tout moment

---

## 🔄 Flow de Données

```
           MATIN (12h)                    APRÈS-MIDI (16h)                  SOIRÉE (17h-23h)
              │                                  │                                  │
    ┌─────────▼─────────┐          ┌────────────▼────────────┐          ┌─────────▼─────────┐
    │ fetch_game_results│          │   fetch_nhl_data        │          │  injury_guardian   │
    │                   │          │                         │          │   (toutes les 30m) │
    │ Récupère résultats│          │ Récupère matchs du jour │          │                    │
    │ des matchs d'hier │          │ Calcule pronos CORTEX   │          │ Détecte blessures  │
    └─────────┬─────────┘          └────────────┬────────────┘          └─────────┬─────────┘
              │                                  │                                  │
              ▼                                  ▼                                  ▼
    ┌──────────────────────────────────────────────────────────────────────────────────┐
    │                              SUPABASE (data_lake)                                │
    │                                                                                  │
    │  Colonnes :                                                                      │
    │  - player_id, name, team, opp, date, ts                                         │
    │  - algo_score_goal, python_prob, python_vol (PRÉDICTIONS)                       │
    │  - result_goal, result_shot (RÉSULTATS RÉELS ← fetch_game_results)             │
    │                                                                                  │
    │  ┌─────────────────────────────────────────────────────────────────┐            │
    │  │ Permet :                                                        │            │
    │  │ • Comparaison Prédiction vs Réalité                            │            │
    │  │ • Calcul ROI (via performance_log)                             │            │
    │  │ • Entraînement ML (améliorer l'algo)                           │            │
    │  └─────────────────────────────────────────────────────────────────┘            │
    └──────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
                              ┌────────────────────┐
                              │   DASHBOARD WEB    │
                              │                    │
                              │ Affiche pronos     │
                              │ du jour en temps   │
                              │ réel (17h-4h30)    │
                              └────────────────────┘
```

---

## 🧪 Tests Manuels

### Test fetch_game_results
```bash
# Tester pour une date spécifique
python3 manage.py fetch_game_results --date 2026-01-07

# Vérifier dans Django shell
python3 manage.py shell
>>> from nhl.models import GameStats
>>> games = GameStats.objects.filter(date='2026-01-07', result_goal__isnull=False)
>>> for g in games[:5]:
...     print(f"{g.name}: pred={g.python_prob}%, result={g.result_goal}")
```

### Test fetch_nhl_data
```bash
python3 manage.py fetch_nhl_data

# Vérifier
>>> games = GameStats.objects.filter(date='2026-01-08')
>>> print(f"Matchs trouvés: {games.count()}")
```

### Test injury_guardian
```bash
python3 manage.py injury_guardian

# Vérifier
>>> injured = GameStats.objects.filter(result_goal='INJURED')
>>> print(f"Joueurs blessés détectés: {injured.count()}")
```

---

## 📊 Monitoring

### Logs à surveiller
```bash
# Résultats quotidiens
tail -f /tmp/cortex_results.log

# Fetching matches
tail -f /tmp/cortex_fetch.log

# Injury tracking
tail -f /tmp/injury_guardian.log
```

### Alertes Recommandées
- Email si `fetch_game_results` trouve 0 matchs (problème API)
- Slack si `injury_guardian` détecte >10 joueurs IR (problème réseau)
- Dashboard Grafana pour visualiser le ROI hebdomadaire

---

## 🚀 Déploiement Production

### 1. Variables d'Environnement
Assurer que `.env` contient :
```
DATABASE_URL=postgresql://...  # Supabase
SECRET_KEY=...
DEBUG=False
```

### 2. Configurer CRON (Production)
```bash
crontab -e
```

Ajouter :
```bash
# CORTEX - Workflow Quotidien
0 12 * * * cd /path/to/nhl-saas && /path/to/venv/bin/python3 manage.py fetch_game_results >> /var/log/cortex_results.log 2>&1
0 16 * * * cd /path/to/nhl-saas && /path/to/venv/bin/python3 manage.py fetch_nhl_data >> /var/log/cortex_fetch.log 2>&1
30 16 * * * cd /path/to/nhl-saas && /path/to/venv/bin/python3 manage.py injury_guardian >> /var/log/injury_guardian.log 2>&1
*/30 17-23 * * * cd /path/to/nhl-saas && /path/to/venv/bin/python3 manage.py injury_guardian >> /var/log/injury_guardian.log 2>&1
```

### 3. Permissions
```bash
chmod +x nhl/management/commands/*.py
```

---

## ✅ Checklist Mise en Production

- [ ] `.env` configuré avec Supabase credentials
- [ ] `schema_performance_log.sql` exécuté dans Supabase
- [ ] CRON jobs configurés (12h, 16h, 16h30, +surveillance)
- [ ] Logs rotatés (`logrotate` configuré)
- [ ] Monitoring en place (Sentry/Grafana)
- [ ] Tests exécutés avec succès
- [ ] Backup Supabase activé

---

**Workflow optimisé pour les matchs NHL (17h30-4h30) !** 🏒
