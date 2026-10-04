-- =========================================================
-- MAP PROJECT DATABASE SCHEMA
-- =========================================================

-- Create database
CREATE DATABASE IF NOT EXISTS MAP_PROJECT;

-- Select database
USE MAP_PROJECT;


-- =========================================================
-- 1. SKU TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS SKU (
    PN VARCHAR(50),
    SKU VARCHAR(50) PRIMARY KEY
);


-- =========================================================
-- 2. PL TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS PL (
    PL VARCHAR(100),
    SKU VARCHAR(50),
    SUB_CATEGORY VARCHAR(50),

    PRIMARY KEY (PL, SKU),

    FOREIGN KEY (SKU)
        REFERENCES SKU(SKU)
);


-- =========================================================
-- 3. PRICE LIST TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS PRICE_LIST (
    PL VARCHAR(100),
    SKU VARCHAR(50),
    MAP DECIMAL(10,2),
    LPP DECIMAL(10,2),

    PRIMARY KEY (PL, SKU),

    FOREIGN KEY (PL, SKU)
        REFERENCES PL(PL, SKU)
);


-- =========================================================
-- 4. SELLER MAPPING TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS SELLER_MAPPING (
    SELLER_NAME VARCHAR(255) PRIMARY KEY,
    HOMOLOGATED_NAME VARCHAR(255)
);


-- =========================================================
-- 5. CATEGORY MAPPING TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS CATEGORY_MAPPING (
    CATEGORY VARCHAR(50),
    SUB_CATEGORY VARCHAR(50),
    PL VARCHAR(100),
    SKU VARCHAR(50) PRIMARY KEY,

    FOREIGN KEY (PL, SKU)
        REFERENCES PL(PL, SKU)
);


-- =========================================================
-- 6. PROMOTION TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS PROMOTION (
    PL VARCHAR(100),
    SKU VARCHAR(50),
    SEASON VARCHAR(10),
    PROMOTION VARCHAR(255),

    PRIMARY KEY (SKU, SEASON),

    FOREIGN KEY (PL, SKU)
        REFERENCES PL(PL, SKU)
);
