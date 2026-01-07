from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentification (Allauth)
    path('nhl/', include('nhl.urls')),
    path('accounts/', include('allauth.urls')),
    
    # Core App (Landing, Dashboard)
    path('', include('core.urls')),
]
