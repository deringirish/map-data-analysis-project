-- ============================================================================
-- Advanced Analytics Query 01: Rolling 7-Day Discount Velocity & Moving Averages
-- Author: Derin Girish
-- Domain: E-Commerce Minimum Advertised Price (MAP) Compliance
-- Technique: Common Table Expressions (CTEs), Window Functions (AVG, SUM, COUNT)
-- ============================================================================

WITH DailyChannelMetrics AS (
    SELECT
        v.Violation_date,
        v.Marketplace,
        v.Category,
        COUNT(v.SKU) AS Daily_Infractions,
        SUM(v.Price_Difference) AS Daily_Total_Deficit_INR,
        AVG(v.Price_Difference) AS Daily_Avg_Deficit_INR,
        AVG((v.Price_Difference / v.MAP_Price) * 100.0) AS Daily_Avg_Discount_Depth_Pct
    FROM
        VIOLATION_TABLE v
    GROUP BY
        v.Violation_date,
        v.Marketplace,
        v.Category
),
MovingWindowAnalysis AS (
    SELECT
        d.Violation_date,
        d.Marketplace,
        d.Category,
        d.Daily_Infractions,
        d.Daily_Total_Deficit_INR,
        d.Daily_Avg_Discount_Depth_Pct,
        
        -- 7-Day Rolling Moving Average of Deficit Severity
        AVG(d.Daily_Total_Deficit_INR) OVER (
            PARTITION BY d.Marketplace, d.Category
            ORDER BY d.Violation_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS Rolling_7Day_Avg_Deficit_INR,
        
        -- 7-Day Cumulative Infraction Velocity
        SUM(d.Daily_Infractions) OVER (
            PARTITION BY d.Marketplace, d.Category
            ORDER BY d.Violation_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS Rolling_7Day_Infraction_Velocity,

        -- 7-Day Trailing Discount Depth Trend
        AVG(d.Daily_Avg_Discount_Depth_Pct) OVER (
            PARTITION BY d.Marketplace, d.Category
            ORDER BY d.Violation_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS Rolling_7Day_Avg_Discount_Pct
    FROM
        DailyChannelMetrics d
)
SELECT
    Violation_date,
    Marketplace,
    Category,
    Daily_Infractions,
    ROUND(Daily_Total_Deficit_INR, 2) AS Daily_Deficit_INR,
    ROUND(Rolling_7Day_Avg_Deficit_INR, 2) AS Rolling_7Day_Deficit_INR,
    Rolling_7Day_Infraction_Velocity,
    ROUND(Rolling_7Day_Avg_Discount_Pct, 2) AS Rolling_Avg_Discount_Pct,
    CASE
        WHEN Daily_Total_Deficit_INR > (Rolling_7Day_Avg_Deficit_INR * 1.5) THEN 'SURGE_ANOMALY'
        WHEN Daily_Total_Deficit_INR < (Rolling_7Day_Avg_Deficit_INR * 0.5) THEN 'POLICY_STABILIZATION'
        ELSE 'BASELINE_BAND'
    END AS Surveillance_Signal
FROM
    MovingWindowAnalysis
ORDER BY
    Marketplace,
    Category,
    Violation_date;
