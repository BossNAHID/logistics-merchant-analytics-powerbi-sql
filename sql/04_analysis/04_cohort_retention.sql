-- Share of each onboarding cohort that placed at least one order in each
-- calendar month after signing up. Zero-activity months are kept in the output.
WITH cohorts AS (
    SELECT
        merchant_id,
        date_trunc('month', onboarding_date)::date AS cohort_month
    FROM merchants
), cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS merchants_in_cohort
    FROM cohorts
    GROUP BY cohort_month
), activity_months AS (
    SELECT generate_series(
        date_trunc('month', MIN(order_date)),
        date_trunc('month', MAX(order_date)),
        interval '1 month'
    )::date AS activity_month
    FROM orders
), merchant_activity AS (
    SELECT DISTINCT
        merchant_id,
        date_trunc('month', order_date)::date AS activity_month
    FROM orders
), cohort_activity AS (
    SELECT
        c.cohort_month,
        a.activity_month,
        COUNT(DISTINCT a.merchant_id) AS active_merchants
    FROM cohorts AS c
    JOIN merchant_activity AS a USING (merchant_id)
    WHERE a.activity_month >= c.cohort_month
    GROUP BY c.cohort_month, a.activity_month
), cohort_grid AS (
    SELECT
        s.cohort_month,
        a.activity_month,
        s.merchants_in_cohort,
        ((EXTRACT(YEAR FROM a.activity_month) - EXTRACT(YEAR FROM s.cohort_month)) * 12
          + EXTRACT(MONTH FROM a.activity_month) - EXTRACT(MONTH FROM s.cohort_month))::integer AS age_month
    FROM cohort_sizes AS s
    CROSS JOIN activity_months AS a
    WHERE a.activity_month >= s.cohort_month
)
SELECT
    g.cohort_month,
    g.activity_month,
    g.age_month,
    g.merchants_in_cohort,
    COALESCE(a.active_merchants, 0) AS active_merchants,
    ROUND(100.0 * COALESCE(a.active_merchants, 0) / g.merchants_in_cohort, 1) AS retention_pct
FROM cohort_grid AS g
LEFT JOIN cohort_activity AS a USING (cohort_month, activity_month)
ORDER BY g.cohort_month, g.age_month;
