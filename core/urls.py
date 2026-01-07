from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Landing page (homepage)
    path('', views.index, name='index'),
    

    
    # Billing
    path('subscribe/', views.CreateCheckoutSessionView.as_view(), name='subscribe'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
