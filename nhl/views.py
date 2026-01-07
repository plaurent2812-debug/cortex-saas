from django.shortcuts import render
from .models import GameStats
from .services import calculate_odds
from .constants import NHL_TEAMS_FULL_NAMES
from datetime import datetime, timedelta
from collections import defaultdict

def dashboard(request):
    """
    NHL Dashboard view - Match-based display with Top 5 scorers per game.
    Shows games from 8PM today to 5AM tomorrow.
    """
    from django.db.models import Q
    
    # 1. Time Filter - Show recent and upcoming games (last 24h + next 24h)
    now = datetime.now()
    past_window = now - timedelta(hours=24)
    future_window = now + timedelta(hours=24)
    
    # Base Query - Games in the time window
    queryset = GameStats.objects.filter(
        algo_score_goal__isnull=False,
        python_prob__isnull=False
    ).filter(
        ts__gte=past_window,
        ts__lte=future_window
    ).order_by('ts', 'team', 'opp')
    
    # Team filter (optional)
    selected_team = request.GET.get('team')
    if selected_team:
        queryset = queryset.filter(Q(team=selected_team) | Q(opp=selected_team))
    
    # 2. Group by Match
    matches = defaultdict(lambda: {
        'team': None,
        'opp': None,
        'time': None,
        'is_home': None,
        'scorers': [],  # For goals
        'playmakers': [],  # For assists (will need python_prob_assist if available)
        'all_players': []
    })
    
    for game in queryset:
        # Create unique match key (normalize team order)
        teams = tuple(sorted([game.team, game.opp]))
        match_key = f"{teams[0]}_vs_{teams[1]}_{game.date}"
        
        # Set match info
        if matches[match_key]['team'] is None:
            matches[match_key]['team'] = game.team if game.is_home else game.opp
            matches[match_key]['opp'] = game.opp if game.is_home else game.team
            matches[match_key]['time'] = game.ts
            matches[match_key]['is_home'] = game.is_home
        
        # Add player with calculated fields
        game.calculated_odds = float(game.result_goal) if game.result_goal and game.result_goal != 'INJURED' else 0.0
        
        matches[match_key]['all_players'].append(game)
        matches[match_key]['scorers'].append(game)  # All players are potential scorers
        matches[match_key]['playmakers'].append(game)  # Same for assists
    
    # 3. Process matches - Top 5 for each category
    processed_matches = []
    for match_key, match_data in matches.items():
        # Sort scorers by python_prob (goal probability)
        top_scorers = sorted(
            match_data['scorers'],
            key=lambda x: x.python_prob if x.python_prob else 0,
            reverse=True
        )[:5]
        
        # For playmakers, we'll use algo_score_shot as proxy (or same python_prob)
        # TODO: If you have python_prob_assist, use that instead
        top_playmakers = sorted(
            match_data['playmakers'],
            key=lambda x: x.algo_score_shot if x.algo_score_shot else 0,
            reverse=True
        )[:5]
        
        # Calculate match context (offensive vs defensive)
        avg_prob = sum(p.python_prob for p in match_data['all_players'] if p.python_prob) / max(len(match_data['all_players']), 1)
        match_context = "Match Offensif 🔥" if avg_prob > 50 else "Match Fermé 🔒" if avg_prob < 30 else "Match Équilibré ⚖️"
        
        processed_matches.append({
            'team': match_data['team'],
            'opp': match_data['opp'],
            'team_full': NHL_TEAMS_FULL_NAMES.get(match_data['team'], match_data['team']),
            'opp_full': NHL_TEAMS_FULL_NAMES.get(match_data['opp'], match_data['opp']),
            'time': match_data['time'],
            'context': match_context,
            'top_scorers': top_scorers,
            'top_playmakers': top_playmakers,
        })
    
    # Sort matches by time
    processed_matches.sort(key=lambda x: x['time'] if x['time'] else datetime.min, reverse=True)
    
    # 4. Apply Freemium Logic
    if not request.user.is_premium:
        # Free users see only first 2 matches
        processed_matches = processed_matches[:2]
        # And only top 3 instead of top 5
        for match in processed_matches:
            match['top_scorers'] = match['top_scorers'][:3]
            match['top_playmakers'] = match['top_playmakers'][:3]
    
    # 5. Team list for filter
    teams = GameStats.objects.values_list('team', flat=True).distinct().order_by('team')
    team_list = [{
        'abbreviation': t,
        'full_name': NHL_TEAMS_FULL_NAMES.get(t, t)
    } for t in teams]
    
    context = {
        'matches': processed_matches,
        'teams': team_list,
        'selected_team': selected_team,
        'is_premium': request.user.is_premium,
    }
    
    # HTMX Response
    if request.headers.get('HX-Request'):
        return render(request, 'nhl/partials/_match_list.html', context)
        
    return render(request, 'nhl/dashboard.html', context)

def player_detail(request, player_id):
    """
    Player detailed analysis page with comprehensive CORTEX insights.
    """
    from django.shortcuts import get_object_or_404
    
    # Get the player's most recent game stats
    game = get_object_or_404(
        GameStats,
        player_id=player_id
    )
    
    # Determine risk level
    risk_level = "Faible"
    risk_color = "green"
    if game.python_vol:
        if game.python_vol > 8.0:
            risk_level = "Élevé"
            risk_color = "red"
        elif game.python_vol > 5.0:
            risk_level = "Moyen"
            risk_color = "orange"
    
    # Determine verdict based on cortex_score
    verdict = "Valeur Standard"
    verdict_color = "blue"
    if game.cortex_score:
        if game.cortex_score > 130:
            verdict = "Valeur Max Extrême 🔥"
            verdict_color = "red"
        elif game.cortex_score > 110:
            verdict = "Excellente Valeur ⭐"
            verdict_color = "yellow"
        elif game.cortex_score > 90:
            verdict = "Bonne Valeur ✓"
            verdict_color = "green"
    
    # Generate context (simplified - could be enhanced with more logic)
    context_text = f"{game.name} joue face à {game.opp}. "
    if game.is_home:
        context_text += "Match à domicile (avantage). "
    else:
        context_text += "Match à l'extérieur. "
    
    if game.cortex_score and game.cortex_score > 120:
        context_text += f"Le score CORTEX de {game.cortex_score}% indique une sous-évaluation majeure par le marché."
    
    context = {
        'game': game,
        'risk_level': risk_level,
        'risk_color': risk_color,
        'verdict': verdict,
        'verdict_color': verdict_color,
        'context_text': context_text,
    }
    
    return render(request, 'nhl/player_detail.html', context)
