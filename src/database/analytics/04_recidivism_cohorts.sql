-- ============================================================================
-- Advanced Analytics Query 04: Recidivism Cohort Survival & Charter Obj. 4 Escalation
-- Author: Derin Girish
-- Domain: E-Commerce Minimum Advertised Price (MAP) Compliance
-- Technique: Cohort Grouping, DENSE_RANK, Survival Ratios, Enforcement Correlation
-- ============================================================================

WITH ResellerFirstBreachCohort AS (
    SELECT
        v.homologated_name AS Corporate_Reseller,
        v.Category,
        MIN(v.Violation_date) AS Cohort_Entry_Date,
        COUNT(DISTINCT v.Violation_date) AS Distinct_Violation_Dates,
        COUNT(v.SKU) AS Lifetime_Infraction_Count,
        SUM(v.Price_Difference) AS Total_Lifetime_Deficit_INR
    FROM
        VIOLATION_TABLE v
    GROUP BY
        v.homologated_name,
        v.Category
),
CohortEnforcementMapping AS (
    SELECT
        c.Cohort_Entry_Date,
        c.Category,
        c.Corporate_Reseller,
        c.Distinct_Violation_Dates,
        c.Lifetime_Infraction_Count,
        c.Total_Lifetime_Deficit_INR,
        
        -- Strike Level Classification
        CASE
            WHEN c.Distinct_Violation_Dates = 1 THEN 'STRIKE_1 (Single Warning)'
            WHEN c.Distinct_Violation_Dates = 2 THEN 'STRIKE_2 (Pre-Suspension Final Warning)'
            ELSE 'STRIKE_3_PLUS (Charter Obj. 4 Suspension)'
        END AS Reseller_Strike_Tier,
        
        CASE WHEN c.Distinct_Violation_Dates >= 3 THEN 1 ELSE 0 END AS Is_Suspended_Entity
    FROM
        ResellerFirstBreachCohort c
),
CohortAggregatedKPIs AS (
    SELECT
        Cohort_Entry_Date,
        Category,
        COUNT(Corporate_Reseller) AS Total_Cohort_Size,
        SUM(CASE WHEN Distinct_Violation_Dates = 1 THEN 1 ELSE 0 END) AS One_Time_Offenders_Reformed,
        SUM(CASE WHEN Distinct_Violation_Dates = 2 THEN 1 ELSE 0 END) AS Two_Time_Offenders_Escalated,
        SUM(Is_Suspended_Entity) AS Chronic_Recidivists_Suspended,
        SUM(Total_Lifetime_Deficit_INR) AS Cohort_Total_Deficit_INR,
        AVG(Total_Lifetime_Deficit_INR) AS Cohort_Avg_Deficit_Per_Entity_INR
    FROM
        CohortEnforcementMapping
    GROUP BY
        Cohort_Entry_Date,
        Category
)
SELECT
    Cohort_Entry_Date,
    Category,
    Total_Cohort_Size,
    One_Time_Offenders_Reformed,
    Two_Time_Offenders_Escalated,
    Chronic_Recidivists_Suspended,
    
    -- Cohort Compliance Rehabilitation Rate (% of sellers who ceased violations after Strike 1)
    ROUND((One_Time_Offenders_Reformed / Total_Cohort_Size) * 100.0, 1) AS Rehabilitation_Rate_Pct,
    
    -- Severe Recidivism Failure Rate (% of sellers who escalated to 30-Day Suspension)
    ROUND((Chronic_Recidivists_Suspended / Total_Cohort_Size) * 100.0, 1) AS Suspension_Escalation_Rate_Pct,
    
    ROUND(Cohort_Total_Deficit_INR, 2) AS Cohort_Total_Deficit_INR,
    ROUND(Cohort_Avg_Deficit_Per_Entity_INR, 2) AS Cohort_Avg_Deficit_INR
FROM
    CohortAggregatedKPIs
ORDER BY
    Cohort_Entry_Date ASC,
    Category ASC;
