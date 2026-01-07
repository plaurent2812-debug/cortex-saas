import math
from dataclasses import dataclass
from typing import Dict, Optional, List, Any

# ==============================================================================
# DATA STRUCTURES
# ==============================================================================

@dataclass
class PlayerSeasonStats:
    games_played: int
    goals: int
    assists: int
    points: int
    shots: int
    position_code: str = "F"

@dataclass
class TeamStats:
    pp_pct: float = 0.20
    l10_pts_pct: float = 0.50

@dataclass
class OpponentStats:
    gaa: float = 3.0
    pk_pct: float = 0.80
    shots_allowed_avg: float = 30.0

@dataclass
class GameContext:
    is_home: bool
    is_opponent_tired: bool = False
    is_team_tired: bool = False
    goalie_form: float = 0.0  # -0.15 to +0.15
    ai_factor: float = 1.0

@dataclass
class OddsResult:
    goal: float
    assist: float
    point: float
    shot_line: float
    shot_odds: float

@dataclass
class ProjectionResult:
    prob_goal: float
    prob_assist: float
    prob_point: float
    prob_shot: float
    score_goal: float
    score_assist: float
    score_point: float
    score_shot: float
    real_odds: OddsResult
    # For data_lake
    algo_score_goal: int
    algo_score_shot: int
    python_prob: float
    python_vol: float

# ==============================================================================
# MATH HELPERS
# ==============================================================================

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))

def clamp01(x: float) -> float:
    return clamp(x, 0.0, 1.0)

def prob_at_least_1(lam: float) -> float:
    """Probability of at least 1 event given lambda (Poisson)."""
    if lam <= 0:
        return 0.0
    return clamp01(1.0 - math.exp(-lam))

def poisson_at_least(k: float, lam: float) -> float:
    """Probability of >= k events given lambda."""
    if lam <= 0:
        return 0.0
    k_int = max(0, int(math.floor(k)))
    if k_int <= 0: # Probability of >= 0 is 100%
        return 1.0
    
    # Sum P(X=i) for i from 0 to k-1
    term = math.exp(-lam)
    sum_prob = term
    for i in range(1, k_int):
        term *= lam / i
        sum_prob += term
        
    return clamp01(1.0 - sum_prob)

# ==============================================================================
# CORE LOGIC
# ==============================================================================

def estimate_realistic_odds(stats: PlayerSeasonStats, is_home: bool) -> OddsResult:
    """
    Port of `estimateRealisticOdds` from Code.gs.
    Calculates realistic odds based on player season stats and location.
    """
    gp = max(1, stats.games_played)
    gpg = stats.goals / gp
    apg = stats.assists / gp
    ppg = stats.points / gp
    spg = stats.shots / gp
    position = stats.position_code

    # 1. COTE BUTEUR 
    odds_goal = 3.50
    if gpg > 0.60: odds_goal = 1.95
    elif gpg > 0.45: odds_goal = 2.30
    elif gpg > 0.30: odds_goal = 2.90
    elif gpg < 0.10: odds_goal = 6.50

    if position == "D":
        odds_goal *= 1.4

    # 2. COTE PASSEUR 
    odds_assist = 2.40
    if apg > 0.70: odds_assist = 1.55
    elif apg > 0.50: odds_assist = 1.85
    elif apg < 0.20: odds_assist = 3.20

    # 3. COTE POINT 
    odds_point = 1.65
    if ppg > 1.30: odds_point = 1.22
    elif ppg > 1.00: odds_point = 1.38
    elif ppg > 0.70: odds_point = 1.62
    elif ppg < 0.40: odds_point = 2.10

    # 4. COTE TIRS 
    shot_line = 2.5
    odds_shot = 1.75
    
    if spg > 3.8:
        shot_line = 3.5
        odds_shot = 1.68
    elif spg > 2.8:
        shot_line = 2.5
        odds_shot = 1.60
    elif spg < 1.8:
        shot_line = 1.5
        odds_shot = 1.55

    # Home/Away Adjustments
    if not is_home:
        odds_goal += 0.10
        odds_point += 0.05

    return OddsResult(
        goal=round(odds_goal, 2),
        assist=round(odds_assist, 2),
        point=round(odds_point, 2),
        shot_line=shot_line,
        shot_odds=round(odds_shot, 2)
    )

def calculate_hybrid_projection(
    player_stats: PlayerSeasonStats,
    team_stats: TeamStats,
    opp_stats: OpponentStats,
    context: GameContext
) -> ProjectionResult:
    """
    Full implementation of `analyzeRoster` logic from Code.gs + `brain_quick` from main.py.
    """
    gp = max(1, player_stats.games_played)
    gpg = player_stats.goals / gp
    apg = player_stats.assists / gp
    ppg = player_stats.points / gp
    spg = player_stats.shots / gp

    # --- P2 : BASE ODDS ---
    real_odds = estimate_realistic_odds(player_stats, context.is_home)

    # --- P3 : CONTEXT FACTORS ---
    # Defensive & Goalie Adjustments
    opp_gaa = max(0.1, opp_stats.gaa)
    def_factor = 1.0 + 0.08 * (opp_gaa - 3.0)
    
    if context.goalie_form != 0:
        def_factor *= (1.0 - context.goalie_form)
        
    def_factor = clamp(def_factor, 0.70, 1.40)
    
    # Fatigue & Home/Away
    home_factor = 1.05 if context.is_home else 0.95
    if context.is_opponent_tired:
        def_factor *= 1.05
    if context.is_team_tired:
        def_factor *= 0.97
        
    # Form & PowerPlay
    form_bonus = 1.04 if team_stats.l10_pts_pct > 0.65 else 1.00
    pp_adv = 1.00
    if team_stats.pp_pct > 0.22 and opp_stats.pk_pct < 0.78:
        pp_adv = 1.08
        
    # --- LAMBDA CALCULATIONS (Standard Model) ---
    lam_goal = gpg * home_factor * def_factor * form_bonus * pp_adv * context.ai_factor
    lam_assist = apg * def_factor * form_bonus * pp_adv * context.ai_factor
    lam_point = ppg * home_factor * def_factor * form_bonus * pp_adv * context.ai_factor
    
    # Shot Lambda
    shot_opp_factor = clamp(1.0 + 0.10 * (opp_gaa - 3.0), 0.85, 1.25)
    lam_shot = spg * home_factor * shot_opp_factor * context.ai_factor
    
    # --- HYBRIDIZATION (Porting 'brain_quick' logic) ---
    # In `Code.gs`, it calls `callPythonBrain` which calls `brain_quick`.
    # `brain_quick` logic is:
    # lam_goal = gpg * home_factor * def_factor (clamped 0-6)
    # math_prob_goal = 1 - exp(-lam_goal)
    # lam_shots = spg * home_factor * opp_shots_factor
    
    # We can refine our lam_goal with the 'Python' specific logic or just trust our extensive `lam_goal` above.
    # The `Code.gs` logic blends them. 
    # Let's perform the specific 'Python Brain' calculations here to get `python_prob` / `python_vol`.
    
    # Python Brain Logic Recreation:
    py_def_factor = clamp(1.0 + 0.08 * (opp_gaa - 3.0), 0.85, 1.25)
    py_lam_goal = clamp(gpg * home_factor * py_def_factor, 0.0, 6.0)
    python_prob_goal = prob_at_least_1(py_lam_goal) * 100.0 # Percentage
    
    opp_shots_allowed = opp_stats.shots_allowed_avg
    py_opp_shots_factor = clamp(1.0 + 0.05 * (opp_shots_allowed - 30.0) / 10.0, 0.90, 1.15)
    python_exp_shots = clamp(spg * home_factor * py_opp_shots_factor, 0.0, 12.0)
    python_vol = python_exp_shots
    
    # --- BLENDING (Hybrid) ---
    # `Code.gs` blends the standard lambda with the python lambda
    # We will simulate this by blending our `lam_goal` with `py_lam_goal`.
    blend_weight = 0.35 # Default weight from Code.gs
    
    # Goal Blending
    # Convert py_prob back to lambda-ish or just blend lambdas
    lam_goal = (1 - blend_weight) * lam_goal + blend_weight * py_lam_goal
    
    # Shot Blending
    lam_shot = (1 - blend_weight) * lam_shot + blend_weight * python_exp_shots
    
    # --- FINAL PROBABILITIES ---
    prob_goal_pct = prob_at_least_1(lam_goal) * 100.0
    prob_assist_pct = prob_at_least_1(lam_assist) * 100.0
    prob_point_pct = prob_at_least_1(lam_point) * 100.0
    
    k_shot = math.floor(real_odds.shot_line) + 1
    prob_shot_pct = poisson_at_least(k_shot, lam_shot) * 100.0
    
    # --- SCORING (Value Calculation) ---
    # Weights are all 1.0 by default in Code.gs
    score_goal = prob_goal_pct * real_odds.goal
    score_assist = prob_assist_pct * real_odds.assist
    score_point = prob_point_pct * real_odds.point
    score_shot = prob_shot_pct * real_odds.shot_odds
    
    return ProjectionResult(
        prob_goal=round(prob_goal_pct, 1),
        prob_assist=round(prob_assist_pct, 1),
        prob_point=round(prob_point_pct, 1),
        prob_shot=round(prob_shot_pct, 1),
        score_goal=round(score_goal, 1),
        score_assist=round(score_assist, 1),
        score_point=round(score_point, 1),
        score_shot=round(score_shot, 1),
        real_odds=real_odds,
        algo_score_goal=int(round(score_goal)),
        algo_score_shot=int(round(score_shot)),
        python_prob=round(python_prob_goal, 1),
        python_vol=round(python_vol, 1)
    )

def calculate_odds(game_stats_obj: Any, is_home: bool) -> float:
    """Wrapper for legacy viewing if needed."""
    return 0.0
