from django.contrib import admin
from .models import GameStats

@admin.register(GameStats)
class GameStatsAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'game_date', 'algo_score_goal', 'calculated_odds_display']
    search_fields = ['name', 'team', 'opp']
    list_filter = ['team', 'is_home']
    ordering = ['-ts', 'name']
    
    def game_date(self, obj):
        return obj.ts.strftime('%Y-%m-%d') if obj.ts else '-'
    
    def calculated_odds_display(self, obj):
        # Only for display purposes in admin
        return obj.calculated_odds
    calculated_odds_display.short_description = "Odds (Est)"
