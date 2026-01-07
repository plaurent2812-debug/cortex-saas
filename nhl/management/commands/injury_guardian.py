"""
Injury Guardian - Automated NHL Injury Tracking System

This management command monitors NHL player injury status and automatically
excludes injured players from predictions by marking their records in the data_lake.

Usage:
    python manage.py injury_guardian

Schedule with CRON (every 30 minutes):
    */30 * * * * cd /path/to/nhl-saas && python manage.py injury_guardian
"""

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from nhl.models import GameStats

BASE_URL = "https://api-web.nhle.com/v1"


class Command(BaseCommand):
    help = 'Monitors NHL injuries and marks injured players in the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('[Injury Guardian] Starting injury check...'))
        
        injured_count = 0
        teams_checked = 0
        
        # Get unique teams from recent predictions
        teams = GameStats.objects.values_list('team', flat=True).distinct()
        
        for team_abbrev in teams:
            if not team_abbrev:
                continue
                
            teams_checked += 1
            self.stdout.write(f"  Checking {team_abbrev}...")
            
            # Fetch roster with injury status
            roster_data = self.fetch_roster(team_abbrev)
            
            if not roster_data:
                continue
            
            # Process injured players
            injured_players = self.extract_injured_players(roster_data)
            
            for player_id in injured_players:
                # Mark all predictions for this player as INJURED
                updated = GameStats.objects.filter(
                    player_id=str(player_id)
                ).update(
                    result_goal='INJURED',
                    result_shot='INJURED'
                )
                
                if updated > 0:
                    injured_count += updated
                    self.stdout.write(
                        self.style.WARNING(f"    ⚠️  Marked {updated} predictions as INJURED for player {player_id}")
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n[Injury Guardian] Complete! Checked {teams_checked} teams, '
                f'marked {injured_count} predictions as injured.'
            )
        )

    def fetch_roster(self, team_abbrev):
        """Fetch team roster with injury status from NHL API"""
        try:
            # Current season roster endpoint
            url = f"{BASE_URL}/roster/{team_abbrev}/current"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.stdout.write(
                    self.style.WARNING(f"    Failed to fetch roster for {team_abbrev}: {response.status_code}")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"    Error fetching roster for {team_abbrev}: {e}")
            )
        
        return None

    def extract_injured_players(self, roster_data):
        """
        Extract player IDs who are currently injured from roster data.
        
        The NHL API includes injury status in various ways:
        - Players on IR (Injured Reserve)
        - Players with injury designations
        """
        injured_ids = []
        
        if not roster_data:
            return injured_ids
        
        # Check forwards
        for player in roster_data.get('forwards', []):
            if self.is_injured(player):
                injured_ids.append(player.get('id'))
        
        # Check defensemen
        for player in roster_data.get('defensemen', []):
            if self.is_injured(player):
                injured_ids.append(player.get('id'))
        
        # Check goalies
        for player in roster_data.get('goalies', []):
            if self.is_injured(player):
                injured_ids.append(player.get('id'))
        
        return injured_ids

    def is_injured(self, player):
        """
        Determine if a player is injured based on their status.
        
        Common injury indicators in NHL API:
        - Status contains "IR" (Injured Reserve)
        - Status contains "OUT"
        - Player has injury designation
        """
        # Check if player has injury status field
        # Note: The exact field may vary by API version
        # This is a defensive implementation
        
        # Method 1: Check for IR status
        status = player.get('status', '').upper()
        if 'IR' in status or 'OUT' in status or 'INJURED' in status:
            return True
        
        # Method 2: Check for injury note/flag
        if player.get('injured', False):
            return True
        
        # Method 3: Check roster status (some APIs use this)
        roster_status = player.get('rosterStatus', '').upper()
        if roster_status in ['IR', 'LTIR', 'IR-NR']:  # LTIR = Long-term IR, IR-NR = Non-roster
            return True
        
        return False
