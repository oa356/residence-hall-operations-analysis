-- Residence Hall Maintenance Operations Analytics
--
-- Load data/processed/maintenance_requests_clean.csv into a table named
-- maintenance_requests_clean before running these queries.

-- 1. Overall operating scorecard
SELECT
    COUNT(*) AS total_requests,
    SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_requests,
    SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_requests,
    ROUND(AVG(assignment_hours), 2) AS avg_assignment_hours,
    ROUND(AVG(resolution_hours), 2) AS avg_resolution_hours,
    ROUND(100.0 * AVG(CASE WHEN within_assignment_sla = 1 THEN 1.0 ELSE 0.0 END), 1) AS assignment_sla_rate_pct,
    ROUND(100.0 * AVG(CASE WHEN reopened = 'Yes' THEN 1.0 ELSE 0.0 END), 1) AS reopen_rate_pct
FROM maintenance_requests_clean;

-- 2. Category demand and performance
SELECT
    category,
    COUNT(*) AS requests,
    ROUND(AVG(assignment_hours), 2) AS avg_assignment_hours,
    ROUND(100.0 * AVG(CASE WHEN within_assignment_sla = 1 THEN 1.0 ELSE 0.0 END), 1) AS assignment_sla_rate_pct,
    ROUND(AVG(resolution_hours), 2) AS avg_resolution_hours,
    ROUND(SUM(estimated_cost_usd), 2) AS estimated_cost_usd
FROM maintenance_requests_clean
GROUP BY category
ORDER BY requests DESC;

-- 3. Hall-level bottlenecks
SELECT
    residence_hall,
    COUNT(*) AS requests,
    SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_requests,
    ROUND(AVG(assignment_hours), 2) AS avg_assignment_hours,
    ROUND(100.0 * AVG(CASE WHEN within_assignment_sla = 1 THEN 1.0 ELSE 0.0 END), 1) AS assignment_sla_rate_pct
FROM maintenance_requests_clean
GROUP BY residence_hall
ORDER BY avg_assignment_hours DESC;

-- 4. Monthly volume trend
SELECT
    submitted_month,
    COUNT(*) AS requests,
    ROUND(AVG(assignment_hours), 2) AS avg_assignment_hours,
    ROUND(100.0 * AVG(CASE WHEN within_assignment_sla = 1 THEN 1.0 ELSE 0.0 END), 1) AS assignment_sla_rate_pct
FROM maintenance_requests_clean
GROUP BY submitted_month
ORDER BY submitted_month;

-- 5. Priority performance
SELECT
    priority,
    COUNT(*) AS requests,
    ROUND(AVG(assignment_hours), 2) AS avg_assignment_hours,
    ROUND(AVG(sla_target_hours), 2) AS sla_target_hours,
    ROUND(100.0 * AVG(CASE WHEN within_assignment_sla = 1 THEN 1.0 ELSE 0.0 END), 1) AS assignment_sla_rate_pct
FROM maintenance_requests_clean
GROUP BY priority
ORDER BY CASE priority
    WHEN 'Emergency' THEN 1
    WHEN 'High' THEN 2
    WHEN 'Medium' THEN 3
    WHEN 'Low' THEN 4
END;

-- 6. Recurring issue types
SELECT
    category,
    subcategory,
    COUNT(*) AS requests,
    ROUND(AVG(assignment_hours), 2) AS avg_assignment_hours,
    ROUND(AVG(resolution_hours), 2) AS avg_resolution_hours
FROM maintenance_requests_clean
GROUP BY category, subcategory
ORDER BY requests DESC
LIMIT 10;
