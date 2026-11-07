-- =========================================================
-- MAP PROJECT DATABASE SCHEMA (3NF RELATIONAL MODEL - SQLITE)
-- Author: Derin Girish D G
-- =========================================================

PRAGMA foreign_keys = ON;

-- 1. SKU TABLE
CREATE TABLE IF NOT EXISTS SKU (
    PN TEXT,
    SKU TEXT PRIMARY KEY
);

-- 2. PL TABLE
CREATE TABLE IF NOT EXISTS PL (
    PL TEXT,
    SKU TEXT,
    SUB_CATEGORY TEXT,
    PRIMARY KEY (PL, SKU),
    FOREIGN KEY (SKU) REFERENCES SKU(SKU) ON DELETE CASCADE
);

-- 3. PRICE LIST TABLE
CREATE TABLE IF NOT EXISTS PRICE_LIST (
    PL TEXT,
    SKU TEXT,
    MAP REAL,
    LPP REAL,
    PRIMARY KEY (PL, SKU),
    FOREIGN KEY (PL, SKU) REFERENCES PL(PL, SKU) ON DELETE CASCADE
);

-- 4. SELLER MAPPING TABLE
CREATE TABLE IF NOT EXISTS SELLER_MAPPING (
    SELLER_NAME TEXT PRIMARY KEY,
    HOMOLOGATED_NAME TEXT
);

-- 5. CATEGORY MAPPING TABLE
CREATE TABLE IF NOT EXISTS CATEGORY_MAPPING (
    CATEGORY TEXT,
    SUB_CATEGORY TEXT,
    PL TEXT,
    SKU TEXT PRIMARY KEY,
    FOREIGN KEY (PL, SKU) REFERENCES PL(PL, SKU) ON DELETE CASCADE
);

-- 6. PROMOTION TABLE
CREATE TABLE IF NOT EXISTS PROMOTION (
    PL TEXT,
    SKU TEXT,
    SEASON TEXT,
    PROMOTION TEXT,
    PRIMARY KEY (SKU, SEASON),
    FOREIGN KEY (PL, SKU) REFERENCES PL(PL, SKU) ON DELETE CASCADE
);

-- 7. SELLER TABLE
CREATE TABLE IF NOT EXISTS SELLER_TABLE (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Seller_name TEXT,
    SKU TEXT,
    Region TEXT,
    Advertised_price REAL,
    Marketplace TEXT,
    Screenshot TEXT,
    Live_link TEXT,
    Last_time_collected DATE
);
CREATE INDEX IF NOT EXISTS idx_seller_sku ON SELLER_TABLE (SKU);
CREATE INDEX IF NOT EXISTS idx_seller_name ON SELLER_TABLE (Seller_name);
CREATE INDEX IF NOT EXISTS idx_collected_date ON SELLER_TABLE (Last_time_collected);

-- 8. PRICE MONITORING TABLE
CREATE TABLE IF NOT EXISTS PRICE_MONITORING_TABLE (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    SKU TEXT,
    Violation_date DATE,
    PL TEXT,
    Category TEXT,
    Sub_category TEXT,
    Region TEXT,
    Marketplace TEXT,
    seller_name TEXT,
    homologated_name TEXT,
    MAP_Price REAL,
    LPP REAL,
    Advertised_price REAL,
    Season TEXT,
    Promotional_price REAL
);
CREATE INDEX IF NOT EXISTS idx_pm_sku ON PRICE_MONITORING_TABLE (SKU);
CREATE INDEX IF NOT EXISTS idx_pm_date ON PRICE_MONITORING_TABLE (Violation_date);
CREATE INDEX IF NOT EXISTS idx_pm_homologated ON PRICE_MONITORING_TABLE (homologated_name);

-- 9. VIOLATION TABLE
CREATE TABLE IF NOT EXISTS VIOLATION_TABLE (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    SKU TEXT,
    Violation_date DATE,
    PL TEXT,
    Category TEXT,
    Sub_category TEXT,
    Region TEXT,
    Marketplace TEXT,
    seller_name TEXT,
    homologated_name TEXT,
    MAP_Price REAL,
    LPP REAL,
    Advertised_price REAL,
    Season TEXT,
    Promotion TEXT,
    Promotional_price REAL,
    Screenshot TEXT,
    Violation_Type TEXT,
    Price_Difference REAL,
    Notice_Doc_Path TEXT
);
CREATE INDEX IF NOT EXISTS idx_vio_sku ON VIOLATION_TABLE (SKU);
CREATE INDEX IF NOT EXISTS idx_vio_date ON VIOLATION_TABLE (Violation_date);
CREATE INDEX IF NOT EXISTS idx_vio_homologated ON VIOLATION_TABLE (homologated_name);
CREATE INDEX IF NOT EXISTS idx_vio_type ON VIOLATION_TABLE (Violation_Type);

-- 10. SUSPENDED CATEGORIES
CREATE TABLE IF NOT EXISTS SUSPENDED_CATEGORIES (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    homologated_name TEXT,
    Category TEXT,
    Total_Infractions INTEGER,
    Distinct_Violation_Dates INTEGER,
    Distinct_SKUs_Violated INTEGER,
    Marketplaces_Audited TEXT,
    Earliest_Violation DATE,
    Latest_Violation DATE,
    Max_Single_Deficit REAL,
    Total_Price_Deficit REAL,
    Enforcement_Status TEXT,
    Legal_Remedy TEXT,
    Suspension_Duration_Days INTEGER,
    Suspension_Effective_Date DATE,
    Suspension_Expiry_Date TEXT
);
CREATE INDEX IF NOT EXISTS idx_susp_seller ON SUSPENDED_CATEGORIES (homologated_name);
CREATE INDEX IF NOT EXISTS idx_susp_cat ON SUSPENDED_CATEGORIES (Category);
CREATE INDEX IF NOT EXISTS idx_susp_status ON SUSPENDED_CATEGORIES (Enforcement_Status);
