-- ============================================================================
-- Advanced Analytics Query 02: Pareto 80/20 Principle & Chronic Offender Concentration
-- Author: Derin Girish
-- Domain: E-Commerce Minimum Advertised Price (MAP) Compliance
-- Technique: DENSE_RANK, Window Running Sums, Cumulative Percentages
-- ============================================================================

WITH ResellerAggregates AS (
    SELECT
        v.homologated_name AS Corporate_Reseller,
        COUNT(v.SKU) AS Total_Infractions,
        COUNT(DISTINCT v.SKU) AS Distinct_SKUs_Violated,
        COUNT(DISTINCT v.Violation_date) AS Infraction_Dates_Count,
        SUM(v.Price_Difference) AS Total_Deficit_INR,
        AVG(v.Price_Difference) AS Avg_Deficit_Per_Infraction_INR
    FROM
        VIOLATION_TABLE v
    GROUP BY
        v.homologated_name
),
ParetoWindow AS (
    SELECT
        r.Corporate_Reseller,
        r.Total_Infractions,
        r.Distinct_SKUs_Violated,
        r.Infraction_Dates_Count,
        r.Total_Deficit_INR,
        r.Avg_Deficit_Per_Infraction_INR,
        
        -- Dense Rank by Margin Deficit Volume
        DENSE_RANK() OVER (ORDER BY r.Total_Deficit_INR DESC) AS Deficit_Rank,
        
        -- Running Cumulative Sum of Deficit
        SUM(r.Total_Deficit_INR) OVER (
            ORDER BY r.Total_Deficit_INR DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS Running_Cumulative_Deficit_INR,
        
        -- Grand Total Fleet Deficit
        SUM(r.Total_Deficit_INR) OVER () AS Grand_Total_Deficit_INR,

        -- Total Entity Count for Percentile Calculations
        COUNT(*) OVER () AS Total_Reseller_Count
    FROM
        ResellerAggregates r
)
SELECT
    Deficit_Rank,
    Corporate_Reseller,
    Total_Infractions,
    Distinct_SKUs_Violated,
    Infraction_Dates_Count,
    ROUND(Total_Deficit_INR, 2) AS Total_Deficit_INR,
    ROUND(Avg_Deficit_Per_Infraction_INR, 2) AS Avg_Deficit_INR,
    ROUND(Running_Cumulative_Deficit_INR, 2) AS Running_Cumulative_Deficit_INR,
    
    -- Cumulative Deficit Share (%)
    ROUND((Running_Cumulative_Deficit_INR / Grand_Total_Deficit_INR) * 100.0, 2) AS Cumulative_Deficit_Share_Pct,
    
    -- Reseller Entity Percentile
    ROUND((Deficit_Rank / Total_Reseller_Count) * 100.0, 2) AS Reseller_Percentile_Rank,
    
    -- Pareto Classification
    CASE
        WHEN (Running_Cumulative_Deficit_INR / Grand_Total_Deficit_INR) <= 0.80 THEN 'PARETO_TIER_1 (Vital 80% Deficit Impact)'
        WHEN (Running_Cumulative_Deficit_INR / Grand_Total_Deficit_INR) <= 0.95 THEN 'PARETO_TIER_2 (Secondary 15% Deficit Impact)'
        ELSE 'PARETO_TIER_3 (Long-Tail Marginal Offender)'
    END AS Enforcement_Priority_Segment
FROM
    ParetoWindow
ORDER BY
    Deficit_Rank;
