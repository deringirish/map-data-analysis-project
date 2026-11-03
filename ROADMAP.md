# 🗺️ Project Enhancement Roadmap & Implementation Milestones

**Project:** Minimum Advertised Price (MAP) Data Analysis & Compliance Engine  
**Domain:** Enterprise E-Commerce Price Auditing, Multi-Currency Normalization & Legal Enforcement  
**Role Positioning:** Senior / Lead Data Analyst  
**Author:** Derin Girish  
**License:** MIT License  
**Repository Status:** Active Portfolio Enhancement  

---

## 🎯 Analytical Vision

This roadmap elevates the core 3NF MySQL warehouse and batch processing engine into an industry-grade **Data Analyst Showcase**. It delivers an interactive stakeholder BI dashboard, advanced analytical SQL views (window functions, cohort analysis, Pareto distributions), and automated executive briefing syntheses.

---

## 📌 Implementation Milestones

### Phase 1: Interactive Stakeholder BI Dashboard (Streamlit & Plotly)
- [x] **Step 1:** Configure `streamlit` and `plotly` dependencies in `pyproject.toml` & establish `ROADMAP.md`
- [x] **Step 2:** Build high-performance data loader & caching engine with MySQL and CSV fallback (`src/dashboard/data_loader.py`)
- [x] **Step 3:** Implement Executive KPI Overview & Multi-Marketplace Filter Shell (`src/dashboard/views/overview.py`)
- [x] **Step 4:** Implement Reseller Surveillance & Recidivism Deep-Dive Hub (`src/dashboard/views/resellers.py`)
- [x] **Step 5:** Implement Interactive Visual Analytics & Price Deficit Drilldown (`src/dashboard/views/analytics.py`)
- [x] **Step 6:** Assemble Master Dashboard (`dashboard.py`) and 1-Click Launch Runner (`run_dashboard.py`)

### Phase 2: Advanced Analytical SQL & Cohort Analytics Suite
- [x] **Step 7:** Author Moving Averages & Discount Velocity Window Queries (`src/database/analytics/01_moving_averages.sql`)
- [x] **Step 8:** Author Pareto 80/20 Chronic Offender Concentration Queries (`src/database/analytics/02_pareto_concentration.sql`)
- [x] **Step 9:** Author Price Cascade & Competitor Undercutting Lead/Lag Queries (`src/database/analytics/03_price_cascades.sql`)
- [x] **Step 10:** Author Recidivism Cohort Survival & Strike Escalation Queries (`src/database/analytics/04_recidivism_cohorts.sql`)

### Phase 3: Automated Board-Ready Executive Briefing
- [ ] **Step 11:** Implement Automated Executive Summary Briefing Generator (`src/reporting/generate_executive_briefing.py`)

### Phase 4: Portfolio Storytelling & Master Orchestration
- [ ] **Step 12:** Update Master CLI Orchestrator (`main.py`) with `--dashboard` and `--briefing` execution flags
- [ ] **Step 13:** Refactor `README.md` with STAR Framework, Live Dashboard preview, and Analytical Architecture
