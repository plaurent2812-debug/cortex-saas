import os
import multiprocessing

# Gunicorn configuration for Cloud Run

# Port d'écoute (Cloud Run injecte PORT env var, défaut 8080)
port = os.getenv('PORT', '8080')
bind = f"0.0.0.0:{port}"

# Nombre de workers
# Pour Cloud Run, on commence souvent avec 2-4 workers selon la config CPU
workers = int(os.getenv('GUNICORN_WORKERS', '2'))
threads = int(os.getenv('GUNICORN_THREADS', '4'))

# Timeout (Cloud Run peut aller jusqu'à 3600s, défaut 60s ici pour sécurité)
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Worker class
# gthread permet de gérer mieux les I/O bloquants (DB calls)
worker_class = 'gthread'

# Reload (dev only)
reload = bool(os.getenv('GUNICORN_RELOAD', False))
