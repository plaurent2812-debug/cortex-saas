-- ============================================================================
-- CORTEX Performance Tracking Schema
-- ============================================================================
-- This schema creates the performance_log table in Supabase to track
-- prediction results and calculate ROI metrics for the CORTEX system.
--
-- Usage:
--   1. Connect to your Supabase project SQL Editor
--   2. Run this script to create the table
--   3. Enable Row Level Security (RLS) if needed
-- ============================================================================

-- Create performance_log table
CREATE TABLE IF NOT EXISTS performance_log (
    id BIGSERIAL PRIMARY KEY,
    
    -- Date and identification
    date DATE NOT NULL,
    player_id TEXT,
    player_name TEXT,
    team TEXT,
    opponent TEXT,
    
    -- Prediction details
    prediction_type TEXT, -- 'GOAL', 'SHOT', 'POINT', 'ASSIST'
    predicted_odds FLOAT,
    algo_score_goal INTEGER,
    python_prob FLOAT,
    cortex_score FLOAT, -- The hybrid score
    
    -- Actual result
    actual_result BOOLEAN, -- TRUE if prediction hit, FALSE if miss
    actual_value TEXT, -- Optional: actual stats (e.g., "2 goals")
    
    -- ROI tracking
    stake FLOAT DEFAULT 1.0, -- Default stake of 1 unit
    profit FLOAT, -- Calculated: (stake * odds) if win, -stake if loss
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes for performance
    CONSTRAINT performance_log_date_idx CHECK (date IS NOT NULL)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_performance_log_date ON performance_log(date DESC);
CREATE INDEX IF NOT EXISTS idx_performance_log_player_id ON performance_log(player_id);
CREATE INDEX IF NOT EXISTS idx_performance_log_result ON performance_log(actual_result);
CREATE INDEX IF NOT EXISTS idx_performance_log_created_at ON performance_log(created_at DESC);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_performance_log_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_performance_log_updated_at
    BEFORE UPDATE ON performance_log
    FOR EACH ROW
    EXECUTE FUNCTION update_performance_log_updated_at();

-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- Overall performance metrics
CREATE OR REPLACE VIEW v_cortex_performance AS
SELECT 
    COUNT(*) as total_predictions,
    COUNT(*) FILTER (WHERE actual_result = TRUE) as wins,
    COUNT(*) FILTER (WHERE actual_result = FALSE) as losses,
    ROUND(
        ((COUNT(*) FILTER (WHERE actual_result = TRUE)::FLOAT / NULLIF(COUNT(*), 0)) * 100)::NUMERIC, 
        2
    ) as win_rate_pct,
    ROUND(SUM(profit)::NUMERIC, 2) as total_profit,
    ROUND(AVG(profit)::NUMERIC, 2) as avg_profit_per_bet,
    ROUND(
        ((SUM(profit) / NULLIF(SUM(stake), 0)) * 100)::NUMERIC,
        2
    ) as roi_pct
FROM performance_log
WHERE actual_result IS NOT NULL;

-- Performance by prediction type
CREATE OR REPLACE VIEW v_performance_by_type AS
SELECT 
    prediction_type,
    COUNT(*) as total_predictions,
    COUNT(*) FILTER (WHERE actual_result = TRUE) as wins,
    ROUND(
        ((COUNT(*) FILTER (WHERE actual_result = TRUE)::FLOAT / NULLIF(COUNT(*), 0)) * 100)::NUMERIC, 
        2
    ) as win_rate_pct,
    ROUND(SUM(profit)::NUMERIC, 2) as total_profit,
    ROUND(
        ((SUM(profit) / NULLIF(SUM(stake), 0)) * 100)::NUMERIC,
        2
    ) as roi_pct
FROM performance_log
WHERE actual_result IS NOT NULL
GROUP BY prediction_type
ORDER BY roi_pct DESC;

-- Weekly performance trend
CREATE OR REPLACE VIEW v_weekly_performance AS
SELECT 
    DATE_TRUNC('week', date) as week_start,
    COUNT(*) as predictions,
    COUNT(*) FILTER (WHERE actual_result = TRUE) as wins,
    ROUND(SUM(profit)::NUMERIC, 2) as profit,
    ROUND(
        ((SUM(profit) / NULLIF(SUM(stake), 0)) * 100)::NUMERIC,
        2
    ) as roi_pct
FROM performance_log
WHERE actual_result IS NOT NULL
GROUP BY DATE_TRUNC('week', date)
ORDER BY week_start DESC;

-- ============================================================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================================================
/*
INSERT INTO performance_log 
    (date, player_id, player_name, team, opponent, prediction_type, 
     predicted_odds, algo_score_goal, python_prob, cortex_score, 
     actual_result, stake, profit)
VALUES
    ('2026-01-07', '8478402', 'Connor McDavid', 'EDM', 'VAN', 'GOAL', 
     2.50, 145, 65.0, 114.0, TRUE, 1.0, 1.50),
    ('2026-01-07', '8477934', 'Auston Matthews', 'TOR', 'MTL', 'GOAL', 
     2.20, 138, 62.0, 107.6, FALSE, 1.0, -1.0),
    ('2026-01-07', '8479318', 'Cale Makar', 'COL', 'DAL', 'POINT', 
     1.60, 152, 70.0, 119.2, TRUE, 1.0, 0.60);
*/

-- ============================================================================
-- ROW LEVEL SECURITY (Optional - if needed for multi-tenancy)
-- ============================================================================
-- Enable RLS if you want to restrict access
-- ALTER TABLE performance_log ENABLE ROW LEVEL SECURITY;

-- Example policy: Allow all authenticated users to read
-- CREATE POLICY "Allow authenticated read" ON performance_log
--     FOR SELECT TO authenticated USING (true);

-- Example policy: Only admins can write
-- CREATE POLICY "Allow admin write" ON performance_log
--     FOR INSERT TO authenticated 
--     WITH CHECK (auth.jwt() ->> 'role' = 'admin');

COMMENT ON TABLE performance_log IS 'Tracks CORTEX prediction results for performance analytics and ROI calculation';
COMMENT ON COLUMN performance_log.cortex_score IS 'Hybrid score: (algo_score_goal * 0.6) + (python_prob * 0.4)';
COMMENT ON COLUMN performance_log.profit IS 'Calculated profit: (stake * odds - stake) if win, -stake if loss';
