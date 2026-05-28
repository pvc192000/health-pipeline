-- Sample Athena queries for verifying the health pipeline data
-- Run these in the Athena console after the Glue crawler has cataloged the data

-- 1. Check row counts per participant
SELECT participant_id, COUNT(*) as days
FROM health_pipeline_db.daily_summaries
GROUP BY participant_id
ORDER BY days DESC
LIMIT 20;

-- 2. Average daily metrics across all participants
SELECT
    AVG(resting_hr) as avg_resting_hr,
    AVG(steps) as avg_steps,
    AVG(sleep_duration) as avg_sleep_min,
    AVG(active_minutes) as avg_active_min
FROM health_pipeline_db.daily_summaries;

-- 3. Sleep patterns by month
SELECT
    month,
    AVG(sleep_duration) as avg_sleep_min,
    AVG(deep_sleep_minutes) as avg_deep_sleep,
    COUNT(*) as records
FROM health_pipeline_db.daily_summaries
GROUP BY month
ORDER BY month;

-- 4. Participants with potential health signals (elevated resting HR + low SpO2)
SELECT
    participant_id,
    date,
    resting_hr,
    spo2_avg,
    skin_temp_deviation
FROM health_pipeline_db.daily_summaries
WHERE resting_hr > 80 AND spo2_avg < 96
ORDER BY date;

-- 5. Activity distribution
SELECT
    CASE
        WHEN steps < 5000 THEN 'sedentary'
        WHEN steps < 10000 THEN 'moderate'
        ELSE 'active'
    END as activity_level,
    COUNT(*) as days,
    AVG(sleep_duration) as avg_sleep
FROM health_pipeline_db.daily_summaries
GROUP BY 1;
