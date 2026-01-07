from django.db import models
from .constants import NHL_TEAMS_FULL_NAMES

class GameStats(models.Model):
    """
    Model representing an NHL player stats from Supabase data_lake table.
    NOTE: The DB table 'data_lake' has NO Primary Key and NO 'id' column.
    We set 'player_id' as primary_key=True to satisfy Django, but we must handle uniqueness manually.
    """
    
    # Player information
    player_id = models.TextField(primary_key=True)  # FAKE PK for Django. Not unique in DB.
    name = models.TextField(db_column='player_name', blank=True, null=True)
    team = models.TextField(blank=True, null=True)
    opp = models.TextField(blank=True, null=True)
    
    # Date information
    date = models.TextField(blank=True, null=True)
    ts = models.DateTimeField(blank=True, null=True)
    
    # Game location
    is_home = models.SmallIntegerField(blank=True, null=True)
    
    # Algorithm scores
    algo_score_goal = models.FloatField(blank=True, null=True)
    algo_score_shot = models.FloatField(blank=True, null=True)
    
    # Probability and volatility (Python)
    python_prob = models.FloatField(blank=True, null=True)
    python_vol = models.FloatField(blank=True, null=True)
    
    # Results
    result_goal = models.TextField(blank=True, null=True)
    # result_shot -> The schema check showed 'result_shot' exists. Use it.
    result_shot = models.TextField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'data_lake'
        ordering = ['-ts', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.date}"
    
    @property
    def is_value_pick(self):
        """Property to identify value picks based on algo score"""
        if self.algo_score_goal is not None:
            return self.algo_score_goal > 130
        return False

    @property
    def team_full_name(self):
        return NHL_TEAMS_FULL_NAMES.get(self.team, self.team)

    @property
    def opp_full_name(self):
        return NHL_TEAMS_FULL_NAMES.get(self.opp, self.opp)

    @property
    def cortex_score(self):
        """
        CORTEX Hybrid Score: Combines algorithm score and Python probability.
        Formula: (algo_score_goal * 0.6) + (python_prob * 0.4)
        Returns a score out of 100.
        """
        if self.algo_score_goal is not None and self.python_prob is not None:
            return round((self.algo_score_goal * 0.6) + (self.python_prob * 0.4), 1)
        return 0.0

    @property
    def success_probability(self):
        """
        Calculate success probability percentage.
        Uses python_prob as primary indicator (already a probability from Poisson).
        Falls back to implied probability from odds if python_prob not available.
        """
        if self.python_prob is not None:
            # python_prob is already a percentage (0-100)
            return round(self.python_prob, 0)
        
        # Fallback: calculate implied probability from odds
        try:
            if self.result_goal and self.result_goal != 'INJURED':
                odds = float(self.result_goal)
                if odds > 0:
                    # Implied probability = 1 / odds * 100
                    return round((1 / odds) * 100, 0)
        except (ValueError, ZeroDivisionError):
            pass
        
        return 0
