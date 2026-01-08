#!/bin/bash
# Railway Post-Deploy Script
# Runs automatically after each deployment

set -e  # Exit on error

echo "🚀 Running post-deployment tasks..."

# 1. Run database migrations
echo "📦 Running migrations..."
python manage.py migrate --noinput

# 2. Create Site for django-allauth (SITE_ID=1)
echo "🌐 Configuring Site for AllAuth..."
python manage.py shell -c "
from django.contrib.sites.models import Site
site, created = Site.objects.get_or_create(
    id=1,
    defaults={'domain': 'web-production-e1695.up.railway.app', 'name': 'CORTEX'}
)
if created:
    print('✅ Site created')
else:
    print('✅ Site already exists')
"

# 3. Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Post-deployment tasks complete!"
