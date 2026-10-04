-- =========================================================
-- MAP PROJECT DATABASE SCHEMA (3NF RELATIONAL MODEL)
-- Author: Derin Girish D G
-- =========================================================

-- Create database
CREATE DATABASE IF NOT EXISTS MAP_PROJECT;

-- Select database
USE MAP_PROJECT;


-- =========================================================
-- 1. SKU TABLE (Product Catalog Master)
-- =========================================================

CREATE TABLE IF NOT EXISTS SKU (
    PN VARCHAR(50),
    SKU VARCHAR(50) PRIMARY KEY
);


-- =========================================================
-- 2. PL TABLE (Product Line Taxonomy)
-- =========================================================

CREATE TABLE IF NOT EXISTS PL (
    PL VARCHAR(100),
    SKU VARCHAR(50),
    SUB_CATEGORY VARCHAR(50),

    PRIMARY KEY (PL, SKU),

    FOREIGN KEY (SKU)
        REFERENCES SKU(SKU)
        ON DELETE CASCADE
);


-- =========================================================
-- 3. PRICE LIST TABLE (Brand Pricing Baselines)
-- =========================================================

CREATE TABLE IF NOT EXISTS PRICE_LIST (
    PL VARCHAR(100),
    SKU VARCHAR(50),
    MAP DECIMAL(12,2),
    LPP DECIMAL(12,2),

    PRIMARY KEY (PL, SKU),

    FOREIGN KEY (PL, SKU)
        REFERENCES PL(PL, SKU)
        ON DELETE CASCADE
);


-- =========================================================
-- 4. SELLER MAPPING TABLE (Entity Homologation)
-- =========================================================

CREATE TABLE IF NOT EXISTS SELLER_MAPPING (
    SELLER_NAME VARCHAR(255) PRIMARY KEY,
    HOMOLOGATED_NAME VARCHAR(255)
);


-- =========================================================
-- 5. CATEGORY MAPPING TABLE (Taxonomy Hierarchy)
-- =========================================================

CREATE TABLE IF NOT EXISTS CATEGORY_MAPPING (
    CATEGORY VARCHAR(50),
    SUB_CATEGORY VARCHAR(50),
    PL VARCHAR(100),
    SKU VARCHAR(50) PRIMARY KEY,

    FOREIGN KEY (PL, SKU)
        REFERENCES PL(PL, SKU)
        ON DELETE CASCADE
);


-- =========================================================
-- 6. PROMOTION TABLE (Seasonal Promotional Rules)
-- =========================================================

CREATE TABLE IF NOT EXISTS PROMOTION (
    PL VARCHAR(100),
    SKU VARCHAR(50),
    SEASON VARCHAR(10),
    PROMOTION VARCHAR(255),

    PRIMARY KEY (SKU, SEASON),

    FOREIGN KEY (PL, SKU)
        REFERENCES PL(PL, SKU)
        ON DELETE CASCADE
);


-- =========================================================
-- 7. SELLER TABLE (Daily Marketplace Surveillance Feed)
-- =========================================================

CREATE TABLE IF NOT EXISTS SELLER_TABLE (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Seller_name VARCHAR(255),
    SKU VARCHAR(50),
    Region VARCHAR(20),
    Advertised_price DECIMAL(12,2),
    Marketplace VARCHAR(50),
    Screenshot VARCHAR(255),
    Live_link TEXT,
    Last_time_collected DATE,

    INDEX idx_seller_sku (SKU),
    INDEX idx_seller_name (Seller_name),
    INDEX idx_collected_date (Last_time_collected)
);


-- =========================================================
-- 8. PRICE MONITORING TABLE (Full Audit Trail - 147,900 Rows)
-- =========================================================

CREATE TABLE IF NOT EXISTS PRICE_MONITORING_TABLE (
    id INT AUTO_INCREMENT PRIMARY KEY,
    SKU VARCHAR(50),
    Violation_date DATE,
    PL VARCHAR(100),
    Category VARCHAR(50),
    Sub_category VARCHAR(50),
    Region VARCHAR(20),
    Marketplace VARCHAR(50),
    seller_name VARCHAR(255),
    homologated_name VARCHAR(255),
    MAP_Price DECIMAL(12,2),
    LPP DECIMAL(12,2),
    Advertised_price DECIMAL(12,2),
    Season VARCHAR(10),
    Promotional_price DECIMAL(12,2),

    INDEX idx_pm_sku (SKU),
    INDEX idx_pm_date (Violation_date),
    INDEX idx_pm_homologated (homologated_name)
);


-- =========================================================
-- 9. VIOLATION TABLE (Enforcement Ledger - 15,936 Rows)
-- =========================================================

CREATE TABLE IF NOT EXISTS VIOLATION_TABLE (
    id INT AUTO_INCREMENT PRIMARY KEY,
    SKU VARCHAR(50),
    Violation_date DATE,
    PL VARCHAR(100),
    Category VARCHAR(50),
    Sub_category VARCHAR(50),
    Region VARCHAR(20),
    Marketplace VARCHAR(50),
    seller_name VARCHAR(255),
    homologated_name VARCHAR(255),
    MAP_Price DECIMAL(12,2),
    LPP DECIMAL(12,2),
    Advertised_price DECIMAL(12,2),
    Season VARCHAR(10),
    Promotion VARCHAR(255),
    Promotional_price DECIMAL(12,2),
    Screenshot VARCHAR(255),
    Violation_Type VARCHAR(100),
    Price_Difference DECIMAL(12,2),

    INDEX idx_vio_sku (SKU),
    INDEX idx_vio_date (Violation_date),
    INDEX idx_vio_homologated (homologated_name),
    INDEX idx_vio_type (Violation_Type)
);
