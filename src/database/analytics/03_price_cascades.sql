-- ============================================================================
-- Advanced Analytics Query 03: Price Cascade & Cross-Marketplace Contagion Tracking
-- Author: Derin Girish
-- Domain: E-Commerce Minimum Advertised Price (MAP) Compliance
-- Technique: LAG, LEAD, FIRST_VALUE, Time-Lapse Price Delta Analysis
-- ============================================================================

WITH SKUPriceSequencing AS (
    SELECT
        v.SKU,
        v.Category,
        v.Violation_date,
        v.Marketplace,
        v.homologated_name AS Reseller_Name,
        v.MAP_Price,
        v.Advertised_price,
        v.Price_Difference AS Deficit_INR,
        
        -- Prior Day Price for Same SKU on Same Channel
        LAG(v.Advertised_price, 1) OVER (
            PARTITION BY v.SKU, v.Marketplace, v.homologated_name
            ORDER BY v.Violation_date
        ) AS Prior_Advertised_Price,
        
        -- Next Day Price Movement
        LEAD(v.Advertised_price, 1) OVER (
            PARTITION BY v.SKU, v.Marketplace, v.homologated_name
            ORDER BY v.Violation_date
        ) AS Next_Advertised_Price,
        
        -- First Initiator of MAP Breach for this SKU
        FIRST_VALUE(v.homologated_name) OVER (
            PARTITION BY v.SKU
            ORDER BY v.Violation_date ASC, v.Price_Difference DESC
        ) AS Cascade_Initiator_Reseller,

        FIRST_VALUE(v.Marketplace) OVER (
            PARTITION BY v.SKU
            ORDER BY v.Violation_date ASC, v.Price_Difference DESC
        ) AS Cascade_Origin_Marketplace,

        -- Market-Wide Minimum Price on this Date
        MIN(v.Advertised_price) OVER (
            PARTITION BY v.SKU, v.Violation_date
        ) AS Day_Lowest_Market_Offer
    FROM
        VIOLATION_TABLE v
)
SELECT
    Violation_date,
    SKU,
    Category,
    Marketplace,
    Reseller_Name,
    ROUND(MAP_Price, 2) AS MAP_Price,
    ROUND(Advertised_price, 2) AS Advertised_Price,
    ROUND(Prior_Advertised_Price, 2) AS Prior_Advertised_Price,
    
    -- Price Step Change from Prior Day
    ROUND(Advertised_price - COALESCE(Prior_Advertised_Price, Advertised_price), 2) AS Daily_Price_Step_Delta,
    
    ROUND(Day_Lowest_Market_Offer, 2) AS Lowest_Market_Offer_INR,
    Cascade_Initiator_Reseller,
    Cascade_Origin_Marketplace,
    
    -- Algorithmic Price Matching Classification
    CASE
        WHEN Reseller_Name = Cascade_Initiator_Reseller AND Marketplace = Cascade_Origin_Marketplace THEN 'CATALYST_PRICE_BREAKER'
        WHEN Advertised_price = Day_Lowest_Market_Offer THEN 'ACTIVE_UNDERCUT_LEADER'
        WHEN Prior_Advertised_Price IS NOT NULL AND Advertised_price < Prior_Advertised_Price THEN 'REACTIVE_CONTAGION_MATCH'
        ELSE 'PASSIVE_DEFICIT_LISTING'
    END AS Competitive_Behavior_Classification
FROM
    SKUPriceSequencing
ORDER BY
    SKU,
    Violation_date,
    Advertised_price ASC;
