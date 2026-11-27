-- =========================================================
-- MAP PROJECT: ANALYTICAL SQL QUERIES (MySQL 8.0)
-- Author: Derin Girish D G
-- Description: Business intelligence queries using CTEs,
-- window functions, Pareto concentration, and rankings.
-- =========================================================

USE MAP_PROJECT;

-- 1. Daily Compliance Rate Trajectory (CTEs + Aggregation)
WITH daily_audits AS (
    SELECT
        Violation_date,
        COUNT(*) AS total_observations
    FROM PRICE_MONITORING_TABLE
    GROUP BY Violation_date
),
daily_violations AS (
    SELECT
        Violation_date,
        COUNT(*) AS violation_count,
        ROUND(SUM(Price_Difference), 2) AS total_deficit_inr
    FROM VIOLATION_TABLE
    GROUP BY Violation_date
)
SELECT
    a.Violation_date,
    a.total_observations,
    COALESCE(v.violation_count, 0) AS violation_count,
    ROUND((a.total_observations - COALESCE(v.violation_count, 0)) * 100.0 / a.total_observations, 2) AS compliance_rate_pct,
    COALESCE(v.total_deficit_inr, 0.00) AS total_deficit_inr
FROM daily_audits a
LEFT JOIN daily_violations v
    ON a.Violation_date = v.Violation_date
ORDER BY a.Violation_date;


-- 2. Marketplace Violation Volume & Financial Deficit Severity
SELECT
    Marketplace,
    COUNT(*) AS total_violations,
    COUNT(DISTINCT homologated_name) AS offending_resellers,
    COUNT(DISTINCT SKU) AS distinct_skus,
    ROUND(SUM(Price_Difference), 2) AS total_deficit_inr,
    ROUND(AVG(Price_Difference), 2) AS avg_deficit_inr,
    ROUND(MAX(Price_Difference), 2) AS max_deficit_inr
FROM VIOLATION_TABLE
GROUP BY Marketplace
ORDER BY total_deficit_inr DESC;


-- 3. 80/20 Pareto Concentration Across Corporate Resellers (Window Functions)
WITH reseller_totals AS (
    SELECT
        homologated_name,
        COUNT(*) AS total_violations,
        ROUND(SUM(Price_Difference), 2) AS reseller_deficit
    FROM VIOLATION_TABLE
    GROUP BY homologated_name
),
pareto_calc AS (
    SELECT
        homologated_name,
        total_violations,
        reseller_deficit,
        SUM(reseller_deficit) OVER (ORDER BY reseller_deficit DESC) AS cumulative_deficit,
        SUM(reseller_deficit) OVER () AS grand_total_deficit,
        RANK() OVER (ORDER BY reseller_deficit DESC) AS deficit_rank
    FROM reseller_totals
)
SELECT
    deficit_rank,
    homologated_name,
    total_violations,
    reseller_deficit,
    ROUND(cumulative_deficit * 100.0 / grand_total_deficit, 2) AS cumulative_deficit_pct
FROM pareto_calc
ORDER BY deficit_rank
LIMIT 20;


-- 4. Top Sub-Categories by Margin Erosion Within Each Category
WITH subcat_summary AS (
    SELECT
        Category,
        Sub_category,
        COUNT(*) AS infraction_count,
        ROUND(SUM(Price_Difference), 2) AS total_deficit_inr
    FROM VIOLATION_TABLE
    GROUP BY Category, Sub_category
)
SELECT
    Category,
    Sub_category,
    infraction_count,
    total_deficit_inr,
    DENSE_RANK() OVER (PARTITION BY Category ORDER BY total_deficit_inr DESC) AS category_rank
FROM subcat_summary
ORDER BY Category, category_rank;


-- 5. Violation Type Breakdown (LPP Breach vs Unauthorized Discount)
SELECT
    Violation_Type,
    COUNT(*) AS incident_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS share_pct,
    ROUND(SUM(Price_Difference), 2) AS total_deficit_inr,
    ROUND(AVG(Price_Difference), 2) AS avg_deficit_inr
FROM VIOLATION_TABLE
GROUP BY Violation_Type
ORDER BY incident_count DESC;


-- 6. Category Suspension Escalation Summary (Charter Objective 4)
SELECT
    Enforcement_Status,
    COUNT(*) AS account_category_pairs,
    SUM(Total_Infractions) AS total_infractions,
    ROUND(SUM(Total_Price_Deficit), 2) AS total_deficit_inr
FROM SUSPENDED_CATEGORIES
GROUP BY Enforcement_Status
ORDER BY total_deficit_inr DESC;
