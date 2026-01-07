from django.urls import path
from . import views

app_name = 'nhl'

urlpatterns = [
    path('dashboard/', views.dashboard, name='nhl_dashboard'),
    path('player/<str:player_id>/', views.player_detail, name='player_detail'),
]
