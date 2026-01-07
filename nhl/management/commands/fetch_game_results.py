"""
NHL Game Results Fetcher
========================
This management command fetches actual game results from the NHL API
and updates the data_lake table with real outcomes for ROI tracking.

Run daily at 12h (noon) to capture previous night's game results.

Usage:
    python manage.py fetch_game_results
    python manage.py fetch_game_results --date 2026-01-07
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from nhl.models import GameStats
import requests
from datetime import datetime, timedelta
import time


class Command(BaseCommand):
    help = 'Fetch actual game results from NHL API and update data_lake'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to check results for (YYYY-MM-DD). Defaults to yesterday.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('[Fetch Results] Starting...'))
        
        # Determine date to check
        if options['date']:
            target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            # Default: yesterday (games from last night)
            target_date = (datetime.now() - timedelta(days=1)).date()
        
        date_str = target_date.strftime('%Y-%m-%d')
        self.stdout.write(f'Checking results for {date_str}')
        
        # 1. Get completed games for the date
        schedule_url = f'https://api-web.nhle.com/v1/schedule/{date_str}'
        try:
            response = requests.get(schedule_url, timeout=10)
            response.raise_for_status()
            schedule = response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to fetch schedule: {e}'))
            return
        
        if 'gameWeek' not in schedule or not schedule['gameWeek']:
            self.stdout.write('No games found for this date')
            return
        
        games_updated = 0
        players_updated = 0
        
        # 2. Process each completed game
        for day in schedule['gameWeek']:
            for game in day.get('games', []):
                if game.get('gameState') not in ['OFF', 'FINAL']:
                    continue  # Skip in-progress or scheduled games
                
                game_id = game['id']
                home_abbrev = game['homeTeam']['abbrev']
                away_abbrev = game['awayTeam']['abbrev']
                
                self.stdout.write(f'  > Processing {away_abbrev} @ {home_abbrev} (Game {game_id})')
                
                # 3. Get boxscore for detailed stats
                boxscore_url = f'https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore'
                try:
                    box_response = requests.get(boxscore_url, timeout=10)
                    box_response.raise_for_status()
                    boxscore = box_response.json()
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'    Failed to fetch boxscore: {e}'))
                    continue
                
                # 4. Extract player stats
                for team_key in ['homeTeam', 'awayTeam']:
                    team_data = boxscore.get(team_key, {})
                    
                    # Forwards
                    for position_group in ['forwards', 'defense']:
                        for player in team_data.get(position_group, []):
                            player_id = str(player.get('playerId'))
                            player_name = player.get('name', {}).get('default', 'Unknown')
                            
                            # Stats
                            goals = player.get('goals', 0)
                            assists = player.get('assists', 0)
                            shots = player.get('shots', 0)
                            
                            # Update in database
                            updated = self.update_player_result(
                                player_id=player_id,
                                player_name=player_name,
                                date=date_str,
                                goals=goals,
                                assists=assists,
                                shots=shots
                            )
                            
                            if updated:
                                players_updated += 1
                
                games_updated += 1
                time.sleep(0.5)  # Rate limiting
        
        self.stdout.write(self.style.SUCCESS(
            f'[Fetch Results] Complete! '
            f'Updated {players_updated} players across {games_updated} games.'
        ))

    def update_player_result(self, player_id, player_name, date, goals, assists, shots):
        """
        Update the data_lake table with actual game results.
        Returns True if updated, False if player not found.
        """
        try:
            # Find predictions for this player on this date
            # Note: player_id is primary key, but there might be date issues
            predictions = GameStats.objects.filter(
                player_id=player_id,
                date=date
            )
            
            if not predictions.exists():
                # Try by name if ID doesn't match
                predictions = GameStats.objects.filter(
                    name__icontains=player_name.split()[-1],  # Last name
                    date=date
                )
            
            if not predictions.exists():
                return False
            
            # Update all matching predictions
            for pred in predictions:
                # Determine if predictions were correct
                # result_goal: 'HIT' if scored, 'MISS' if didn't
                # result_shot: 'HIT' if met shot threshold, 'MISS' if didn't
                
                if goals > 0:
                    pred.result_goal = 'HIT'
                else:
                    pred.result_goal = 'MISS'
                
                # For shots, we'd need to know the line (threshold)
                # For now, just store the actual count
                pred.result_shot = str(shots)
                
                pred.save()
                
                self.stdout.write(
                    f'    ✓ {player_name}: {goals}G, {assists}A, {shots}SOG '
                    f'(Predicted prob: {pred.python_prob}%)'
                )
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Error updating {player_name}: {e}'))
            return False
