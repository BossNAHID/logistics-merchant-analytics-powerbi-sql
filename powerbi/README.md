# Power BI handoff

This folder is the build spec for the Desktop report. The project is currently SQL-first; no fake or empty `.pbix` is checked in. Build and save the report in Power BI Desktop as `powerbi/delivery_analytics.pbix` when a Windows Desktop session is available.

## Model

Use Import mode for this sample. Load these PostgreSQL views from `sql/03_views.sql` and rename the queries in Power Query so the measure names below stay readable:

| SQL view | Power BI table name |
| --- | --- |
| `vw_fact_orders` | `fact_orders` |
| `vw_fact_issues` | `fact_issues` |
| `vw_dim_merchant` | `dim_merchant` |
| `vw_dim_hub` | `dim_hub` |
| `vw_dim_kam` | `dim_kam` |

Create a date table from the actual data range so late-October issues that opened in November are included:

```DAX
dim_date =
ADDCOLUMNS (
    CALENDAR (
        MINX ( fact_orders, fact_orders[order_date] ),
        MAXX ( fact_issues, fact_issues[opened_date] )
    ),
    "Year", YEAR ( [Date] ),
    "Month Number", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM" ),
    "Year Month", FORMAT ( [Date], "YYYY-MM" )
)
```

Mark `dim_date` as the date table using `[Date]`. Sort `[Month]` by `[Month Number]`; use `[Year Month]` on month-axis visuals.

Relationships should be one-to-many, single direction, from dimensions to facts:

- `dim_date[Date]` → `fact_orders[order_date]`
- `dim_date[Date]` → `fact_issues[opened_date]`
- `dim_merchant[merchant_id]` → both fact tables
- `dim_hub[hub_id]` → both fact tables
- `dim_kam[kam_id]` → both fact tables

Keep the model as a star. Don't add a second path from KAM through merchant to facts; `kam_id` is already present on both fact views.

## Measures

`measures.dax` contains 18 starter measures. The churn flag is intended for a merchant-level table, and the return/success measures use all orders as their denominator. Format the rate measures as percentages and revenue as BDT (৳) with thousands separators.

## Three pages

### 1. Executive overview

- Cards: total orders, delivery success rate, return rate, COD collection rate and delivered-fee revenue.
- Line chart: orders and recognized revenue by `Year Month` (use a second axis or separate visuals so the scales remain legible).
- Column chart: revenue by division.
- Bar or treemap: delivered orders and revenue by merchant category.
- Slicers: date, category, KAM and hub.

### 2. Merchant health

- Slicers: KAM and category.
- Table: merchant, tier, latest three-month orders, prior three-month orders, change and churn-risk flag.
- A small-multiple or line chart for monthly merchant order volume; keep the chosen merchant in filter context.
- Drill-through page for one merchant with order trend, delivery outcomes, fee revenue and open issues.

The SQL churn query applies the project's exact threshold (prior window at least 20 orders; latest window down more than 30%). The DAX flag is a useful interactive counterpart; use the SQL list when you need a fixed extract.

### 3. Operations

- Hub bar chart sorted by average delivery days, with order count in tooltip so low-volume hubs don't look more certain than they are.
- Failure and return rates by hub or division.
- Issue volume by issue type and average resolution hours; show open issues separately from resolved-ticket duration.
- Delivery-time distribution (histogram or bins) and a clear note that the regression lives at hub level.

Import `theme.json` from **View → Themes → Browse for themes**. Use descriptive titles (for example, “Barishal and Rangpur average longer routes”) only if the current filter context supports the statement; otherwise stick to neutral labels such as “Average delivery days by hub.”
