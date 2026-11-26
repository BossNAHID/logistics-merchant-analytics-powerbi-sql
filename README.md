# Delivery performance & merchant analytics

A small portfolio project built around a familiar logistics question: **where are parcels getting stuck, and which merchants need a conversation before they quietly stop shipping?** The example company, merchants, hubs and orders are fictional. The dataset is synthetic from end to end; it contains no Carrybee or other real-company data.

The project brief called for a full path from data generation to SQL analysis and a three-page Power BI report. This repository contains the repeatable dataset, PostgreSQL model and queries, a compact statistics exercise, and the Power BI model/report handoff. Power BI Desktop is Windows-only, so a `.pbix` is not included; the model, measures, theme and page plan are ready for the Desktop build.

## What is in here

```text
data/                 checked-in synthetic CSVs used by the SQL load script
generator/            repeatable data generator
sql/                  PostgreSQL schema, CSV load, reporting views, analysis queries
analysis/             hub-level regression, moving-average forecast, saved results
powerbi/              DAX measures, theme, model and report instructions
tests/                generator and analysis checks
```

The current sample covers **November 2025 to October 2026**: 300 merchants, 8 account managers, 12 hubs, about 60,000 orders and about 8,000 support issues. A fixed seed creates a new copy of the same sample, including its merchant names and order mix.

## A few definitions, before the charts

- **Delivery success rate:** delivered orders divided by all orders placed.
- **Return rate:** returned orders divided by all orders placed.
- **Average delivery days:** mean recorded delivery days; cancelled orders have no delivery duration.
- **COD collection rate:** delivered COD orders collected divided by delivered orders with a COD amount. Prepaid parcels are not in the denominator.
- **Revenue:** delivery fees on delivered parcels. COD is collected on a merchant's behalf, so it is not treated as courier revenue.
- **Churn-risk flag:** at least 20 orders in the prior three calendar months, followed by a drop greater than 30% in the latest three calendar months.

Those choices are explicit so a reviewer can disagree with the definition without guessing what a measure means.

## Run it locally

### 1. Generate or keep the supplied sample

The CSVs are already in `data/`. To recreate them with the default seed:

```bash
python -m venv .venv
. .venv/bin/activate            # Windows PowerShell: .venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
python generator/generate_data.py
```

The generator accepts `--seed`, `--target-orders` and `--output-dir`. For a quick, isolated run:

```bash
python generator/generate_data.py --seed 731 --target-orders 4500 --output-dir /tmp/delivery-sample
```

A target is an expected volume, not an exact row limit; ordinary Poisson variation is part of the sample design.

### 2. Load PostgreSQL

Create an empty database, then run these from the repository root. The `\copy` paths in the load file are relative to the `psql` working directory.

```bash
createdb delivery_analytics
psql -v ON_ERROR_STOP=1 -d delivery_analytics -f sql/01_schema.sql
psql -v ON_ERROR_STOP=1 -d delivery_analytics -f sql/02_load.sql
psql -v ON_ERROR_STOP=1 -d delivery_analytics -f sql/03_views.sql
```

The schema intentionally does not drop existing tables. Use a fresh database for a clean run; the load script is not meant to be replayed on populated tables. Example analysis queries are separate files under `sql/04_analysis/` and can be run individually, for example:

```bash
psql -d delivery_analytics -f sql/04_analysis/03_churn_risk.sql
```

### 3. Run the statistical check and tests

```bash
python analysis/analyze_delivery.py
python -m unittest discover -s tests -v
```

The analysis writes three CSVs and a JSON summary under `analysis/results/`. The regression is intentionally at **hub level**: average delivery days versus the share of orders returned. The current synthetic sample has a strong positive association, but that is a property of the data-generation rules—not evidence that delivery time alone causes returns. The forecast is the average monthly volume of the latest three months, held flat for three periods. It is a baseline, not a planning-grade model.

## What this sample shows

For the checked-in seed, the generator produced 59,487 orders and 7,815 issues. Volume peaks in October 2026 (5,982 orders) and is lowest in February (3,849), reflecting the seasonal curve built into the sample. Barishal Sadar is the slowest hub at about 3.7 days on average; Rangpur Sadar follows at about 3.5 days. The hub-level correlation between delivery days and return rate is 0.97. That last result is deliberately planted and belongs in the methodology notes, not in a claim about real courier performance.

## Power BI build

1. Connect Power BI Desktop to PostgreSQL and import `vw_fact_orders`, `vw_fact_issues`, `vw_dim_merchant`, `vw_dim_hub` and `vw_dim_kam` (created by `sql/03_views.sql`). Rename the imported queries without the `vw_` prefix to match the DAX table names.
2. Create a date table that spans order dates through issue-open dates, mark it as the date table, and sort `Month` by `Month Number`. The full DAX starter and relationship map are in [`powerbi/README.md`](powerbi/README.md).
3. Add one-to-many, single-direction relationships from the dimensions to both facts: date to each fact's date field, merchant to both facts, hub to both facts and KAM to both facts. Keep the model as a star; `kam_id` is already present in both fact views.
4. Add the measures in `powerbi/measures.dax` and import `powerbi/theme.json`.

### Report pages

- **Executive overview:** KPI cards for orders, success, returns, COD collection and revenue; monthly order/revenue trend; revenue by division; category mix.
- **Merchant health:** KAM and category slicers; churn-risk table; merchant monthly change; a drill-through merchant profile with order, revenue and issue history.
- **Operations:** hub ranking by delivery time and failure rate; district/division view; issue mix and resolution-time distribution.

Keep the page labels plain. A KAM should be able to see the merchants to call; an operations lead should be able to find the hub to investigate. Avoid putting the regression or the three-month forecast in a headline KPI card without its caveat.

## Selected SQL work

The individual queries cover:

- month-over-month merchant volume (including zero-order months);
- merchant revenue rank and top decile;
- churn-risk list using two adjacent three-month windows;
- onboarding cohort retention;
- hub service levels;
- issue resolution time by issue type; and
- monthly revenue with a running total.

Revenue is purposefully kept separate from COD. `vw_monthly_delivery_metrics` contains the reusable monthly KPIs; `vw_fact_orders` and `vw_fact_issues` are the Power BI facts.

## Validation and limits

The tests check that the generator is repeatable for a fixed seed, related CSV IDs join up, statuses are valid, and the analysis produces a three-month forecast plus the hub-level regression outputs. The supplied database scripts target PostgreSQL. The Power BI model still needs to be assembled and checked in Power BI Desktop, then saved as `powerbi/delivery_analytics.pbix`; screenshots and a portfolio page are follow-up presentation work.

All names, districts, volumes and prices are fabricated. The data has intentionally planted seasonality, merchant growth/decline, churn-like drops, slower hubs, and a positive delivery-time/return relationship so the analysis has something to find. It should not be used to describe real Bangladesh delivery performance.
