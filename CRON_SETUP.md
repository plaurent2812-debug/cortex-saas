# 🤖 Configuration CRON - CORTEX Automation

## 📅 Planning Quotidien

### 12h00 - Récupération des Résultats
Récupère les résultats réels des matchs de la veille et met à jour la `performance_log`

### 16h00 - Génération Prédictions
Analyse les matchs du jour et génère les prédictions CORTEX

### 16h30 - Surveillance Blessures  
Vérifie les mises à jour de blessures via ESPN API

---

## ⚙️ Configuration CRON (macOS)

### Option 1 : CRON Système (Recommandé pour serveur)

1. **Ouvre l'éditeur CRON** :
```bash
crontab -e
```

2. **Ajoute ces 3 lignes** (appuie sur `i` pour éditer) :
```cron
# CORTEX - NHL Data Automation
0 12 * * * cd /Users/pierrelaurent/Desktop/nhl-saas && /Users/pierrelaurent/Desktop/nhl-saas/venv/bin/python manage.py fetch_game_results >> /Users/pierrelaurent/Desktop/nhl-saas/logs/cron_results.log 2>&1
0 16 * * * cd /Users/pierrelaurent/Desktop/nhl-saas && /Users/pierrelaurent/Desktop/nhl-saas/venv/bin/python manage.py fetch_nhl_data >> /Users/pierrelaurent/Desktop/nhl-saas/logs/cron_data.log 2>&1
30 16 * * * cd /Users/pierrelaurent/Desktop/nhl-saas && /Users/pierrelaurent/Desktop/nhl-saas/venv/bin/python manage.py injury_guardian >> /Users/pierrelaurent/Desktop/nhl-saas/logs/cron_injuries.log 2>&1
```

3. **Sauvegarde et quitte** :
   - Appuie sur `Esc`
   - Tape `:wq` puis `Entrée`

4. **Vérifie l'installation** :
```bash
crontab -l
```

---

### Option 2 : launchd (macOS natif)

Si CRON ne fonctionne pas sur macOS (permissions), utilise **launchd**.

#### Crée 3 fichiers `.plist` :

**1. Résultats (12h)** :
```bash
nano ~/Library/LaunchAgents/com.cortex.fetch_results.plist
```
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cortex.fetch_results</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/pierrelaurent/Desktop/nhl-saas/venv/bin/python</string>
        <string>/Users/pierrelaurent/Desktop/nhl-saas/manage.py</string>
        <string>fetch_game_results</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>12</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>/Users/pierrelaurent/Desktop/nhl-saas</string>
</dict>
</plist>
```

**2. Prédictions (16h)** :
```bash
nano ~/Library/LaunchAgents/com.cortex.fetch_data.plist
```
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cortex.fetch_data</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/pierrelaurent/Desktop/nhl-saas/venv/bin/python</string>
        <string>/Users/pierrelaurent/Desktop/nhl-saas/manage.py</string>
        <string>fetch_nhl_data</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>16</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>/Users/pierrelaurent/Desktop/nhl-saas</string>
</dict>
</plist>
```

**3. Blessures (16h30)** :
```bash
nano ~/Library/LaunchAgents/com.cortex.injury_guardian.plist
```
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cortex.injury_guardian</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/pierrelaurent/Desktop/nhl-saas/venv/bin/python</string>
        <string>/Users/pierrelaurent/Desktop/nhl-saas/manage.py</string>
        <string>injury_guardian</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>16</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>/Users/pierrelaurent/Desktop/nhl-saas</string>
</dict>
</plist>
```

**Charge les tâches** :
```bash
launchctl load ~/Library/LaunchAgents/com.cortex.fetch_results.plist
launchctl load ~/Library/LaunchAgents/com.cortex.fetch_data.plist
launchctl load ~/Library/LaunchAgents/com.cortex.injury_guardian.plist
```

**Vérifie le statut** :
```bash
launchctl list | grep cortex
```

---

## 🧪 Test Manuel

Avant d'automatiser, teste chaque script manuellement :

```bash
cd /Users/pierrelaurent/Desktop/nhl-saas
source venv/bin/activate

# Test 1 : Récupération résultats
python manage.py fetch_game_results

# Test 2 : Génération prédictions
python manage.py fetch_nhl_data

# Test 3 : Surveillance blessures
python manage.py injury_guardian
```

---

## 📊 Monitoring

### Créer le dossier logs :
```bash
mkdir -p /Users/pierrelaurent/Desktop/nhl-saas/logs
```

### Consulter les logs :
```bash
# Résultats
tail -f logs/cron_results.log

# Prédictions
tail -f logs/cron_data.log

# Blessures
tail -f logs/cron_injuries.log
```

---

## 🚨 Troubleshooting

### CRON ne s'exécute pas ?
1. Vérifie les permissions : `ls -la ~/Library/LaunchAgents/`
2. Vérifie les erreurs : `tail -f /var/log/system.log | grep cortex`
3. Utilise des chemins absolus (pas de `~/` dans CRON)

### Variables d'environnement manquantes ?
Les CRON jobs n'ont pas accès au `.env` par défaut. Solutions :
- **Option A** : Charge `.env` dans chaque script
- **Option B** : Spécifie les variables dans le `.plist`

---

## ✅ Checklist Post-Installation

- [ ] Dossier `logs/` créé
- [ ] CRON ou launchd configuré
- [ ] Tests manuels réussis
- [ ] Logs accessibles
- [ ] Monitoring actif pendant 24h

🎯 **Production Ready** une fois cette checklist complétée !
