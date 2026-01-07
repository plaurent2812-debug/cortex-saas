import requests
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from nhl.models import GameStats
from nhl.services import (
    calculate_hybrid_projection, 
    PlayerSeasonStats, 
    TeamStats, 
    OpponentStats, 
    GameContext
)

BASE_URL = "https://api-web.nhle.com/v1"

class Command(BaseCommand):
    help = 'Fetches NHL data, calculates projections, and updates the Data Lake.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting NHL Data Ingestion...'))
        
        # 1. Determine Date (ET)
        # Simplified: Use current date
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 2. Fetch Schedule
        schedule = self.fetch_json(f"{BASE_URL}/schedule/now")
        if not schedule or 'gameWeek' not in schedule:
            self.stdout.write(self.style.ERROR('Failed to fetch schedule.'))
            return

        # Find today's games (or closest playing date in the response)
        # The API returns a week. We want the one matching 'today' or the first one with games.
        day_data = None
        for day in schedule['gameWeek']:
            if day['date'] == today:
                day_data = day
                break
        
        # Fallback: if no games today (or we ran it late/early), find next games
        if not day_data and schedule['gameWeek']:
             # Just picking the first day for demo/testing purposes if today is empty
             day_data = schedule['gameWeek'][0]
             today = day_data['date'] # Update today to the game date
        
        if not day_data or not day_data.get('games'):
            self.stdout.write(self.style.WARNING(f'No games found for {today}.'))
            return

        self.stdout.write(f"Processing {len(day_data['games'])} games for {today}...")

        # 3. Fetch Context (Standings for Team Stats)
        standings_data = self.fetch_json(f"{BASE_URL}/standings/now")
        team_context = self.process_standings(standings_data)

        # 4. Process Games
        for game in day_data['games']:
            home_team = game['homeTeam']['abbrev']
            away_team = game['awayTeam']['abbrev']
            
            self.stdout.write(f"  > Analyzing {home_team} vs {away_team}")
            
            # Analyze Home Team
            self.process_team(home_team, away_team, True, team_context, today)
            
            # Analyze Away Team
            self.process_team(away_team, home_team, False, team_context, today)

        self.stdout.write(self.style.SUCCESS(f'Successfully processed data for {today}.'))

    def fetch_json(self, url):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching {url}: {e}"))
        return None

    def process_standings(self, standings_json):
        context = {}
        if not standings_json or 'standings' not in standings_json:
            return context
            
        for team in standings_json['standings']:
            abbrev = team['teamAbbrev']['default']
            
            ga = team.get('goalAgainst', 0)
            gp = max(1, team.get('gamesPlayed', 1))
            gaa = ga / gp
            
            context[abbrev] = {
                'gaa': gaa,
                'pp_pct': team.get('powerPlayPctg', 0.20),
                'pk_pct': team.get('penaltyKillPctg', 0.80),
                'l10_pts_pct': team.get('l10PtsPctg', 0.50),
                'shots_allowed': 30.0 # Placeholder, API v1 standings might not have shots allowed explicit
            }
        return context

    def process_team(self, team, opp, is_home, context_map, date_str):
        # Fetch Roster Stats
        roster_stats = self.fetch_json(f"{BASE_URL}/club-stats/{team}/now")
        if not roster_stats or 'skaters' not in roster_stats:
            self.stdout.write(self.style.WARNING(f"    No stats found for {team}"))
            return

        # Context objects
        my_ctx = context_map.get(team, {})
        opp_ctx = context_map.get(opp, {})
        
        t_stats = TeamStats(
            pp_pct=my_ctx.get('pp_pct', 0.20),
            l10_pts_pct=my_ctx.get('l10_pts_pct', 0.50)
        )
        
        o_stats = OpponentStats(
            gaa=opp_ctx.get('gaa', 3.0),
            pk_pct=opp_ctx.get('pk_pct', 0.80),
            shots_allowed_avg=opp_ctx.get('shots_allowed', 30.0)
        )
        
        game_ctx = GameContext(
            is_home=is_home,
            is_opponent_tired=False, # TODO: Implement tired logic
            is_team_tired=False # TODO: Implement tired logic
        )
        
        # Iterate Skaters
        count = 0
        for p in roster_stats['skaters']:
            # Filters
            if p.get('gamesPlayed', 0) <= 5:
                continue
            
            # Construct Player Stats
            try:
                p_stats = PlayerSeasonStats(
                    games_played=p.get('gamesPlayed', 0),
                    goals=p.get('goals', 0),
                    assists=p.get('assists', 0),
                    points=p.get('points', 0),
                    shots=p.get('shots', 0),
                    position_code=p.get('positionCode', 'F')
                )
                
                # Run Engine
                proj = calculate_hybrid_projection(p_stats, t_stats, o_stats, game_ctx)
                
                # Check for Value (Score > 40)
                if proj.score_point > 40 or proj.score_shot > 40:
                    player_id = str(p.get('id', p.get('playerId')))
                    
                    # Upsert to DB (Manual Handling for Heap Table)
                    # We check if a record exists for this player AND date.
                    defaults = {
                        'name': f"{p.get('firstName', {}).get('default', '')} {p.get('lastName', {}).get('default', '')}",
                        'team': team,
                        'opp': opp,
                        'ts': timezone.now(),
                        'is_home': 1 if is_home else 0,
                        'algo_score_goal': proj.algo_score_goal,
                        'algo_score_shot': proj.algo_score_shot,
                        'python_prob': proj.python_prob,
                        'python_vol': proj.python_vol,
                        'result_goal': str(proj.real_odds.goal),
                        'result_shot': str(proj.real_odds.shot_odds)
                    }

                    exists = GameStats.objects.filter(player_id=player_id, date=date_str).exists()
                    if exists:
                        GameStats.objects.filter(player_id=player_id, date=date_str).update(**defaults)
                    else:
                        GameStats.objects.create(player_id=player_id, date=date_str, **defaults)
                        
                    count += 1
            except Exception as e:
                # self.stdout.write(f"    Error processing player {p.get('id')}: {e}")
                pass
        
        self.stdout.write(f"    -> Saved {count} players for {team}")
