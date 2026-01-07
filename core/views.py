from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import get_user_model
import stripe
import logging


# Ensure models are imported (though not strictly used in new views except User models)
# from .models import Player  <-- Removed

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

def index(request):
    """
    Landing page publique avec ticker de résultats et graphique de performance.
    """
    from nhl.models import GameStats
    from datetime import datetime, timedelta
    
    # Fetch recent winning predictions for ticker (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_wins = GameStats.objects.filter(
        result_goal__isnull=False,
        algo_score_goal__gte=130  # Value picks only
    ).exclude(
        result_goal='INJURED'
    ).order_by('-ts')[:10]
    
    # Mock performance data for chart (replace with real data from performance_log)
    # Format: [week_label, cortex_roi, public_avg]
    performance_data = [
        ['Sem 1', 12.5, -2.3],
        ['Sem 2', 18.2, 1.5],
        ['Sem 3', 15.8, -1.0],
        ['Sem 4', 22.1, 3.2],
        ['Sem 5', 19.5, 0.8],
    ]
    
    context = {
        'recent_wins': recent_wins,
        'performance_data': performance_data,
    }
    
    return render(request, 'index.html', context)


@method_decorator(login_required, name='dispatch')
class CreateCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        domain_url = request.build_absolute_uri('/')[:-1] # Remove trailing slash
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': settings.STRIPE_PRICE_ID,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=domain_url + '/nhl/dashboard/?payment=success',
                cancel_url=domain_url + '/nhl/dashboard/?payment=cancelled',
                client_reference_id=request.user.id,
                customer_email=request.user.email,
            )
            return redirect(checkout_session.url)
        except Exception as e:
            return JsonResponse({'error': str(e)})

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] in ['checkout.session.completed', 'invoice.payment_succeeded']:
        session = event['data']['object']
        
        # Get user
        client_reference_id = session.get('client_reference_id')
        stripe_customer_id = session.get('customer')
        
        User = get_user_model()
        
        try:
            if client_reference_id:
                user = User.objects.get(id=client_reference_id)
                user.is_premium = True
                user.stripe_customer_id = stripe_customer_id
                user.save()
                logger.info(f"User {user.email} marked as premium via Webhook.")
        except User.DoesNotExist:
            logger.error(f"User with ID {client_reference_id} not found during webhook processing.")

    return HttpResponse(status=200)
