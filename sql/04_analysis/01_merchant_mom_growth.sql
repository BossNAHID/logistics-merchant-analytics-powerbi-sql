-- Calendar month-over-month order change for every merchant.
-- The month scaffold means an inactive month is shown as zero, not skipped.
WITH month_range AS (
    SELECT generate_series(
        date_trunc('month', MIN(order_date))::date,
        date_trunc('month', MAX(order_date))::date,
        interval '1 month'
    )::date AS month
    FROM orders
), merchant_months AS (
    SELECT
        m.merchant_id,
        m.merchant_name,
        r.month,
        COUNT(o.order_id) AS order_count
    FROM merchants AS m
    CROSS JOIN month_range AS r
    LEFT JOIN orders AS o
        ON o.merchant_id = m.merchant_id
       AND date_trunc('month', o.order_date)::date = r.month
    GROUP BY m.merchant_id, m.merchant_name, r.month
), with_previous_month AS (
    SELECT
        *,
        LAG(order_count) OVER (PARTITION BY merchant_id ORDER BY month) AS previous_month_orders
    FROM merchant_months
)
SELECT
    merchant_id,
    merchant_name,
    month,
    order_count,
    previous_month_orders,
    ROUND(
        100.0 * (order_count - previous_month_orders) / NULLIF(previous_month_orders, 0),
        1
    ) AS month_over_month_change_pct
FROM with_previous_month
ORDER BY merchant_id, month;
