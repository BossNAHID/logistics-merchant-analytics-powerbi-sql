-- Cumulative delivery-fee revenue by month. Months with no completed deliveries
-- stay visible so the running total does not quietly skip a period.
WITH calendar AS (
    SELECT generate_series(
        date_trunc('month', MIN(order_date))::date,
        date_trunc('month', MAX(order_date))::date,
        interval '1 month'
    )::date AS month
    FROM orders
), monthly_revenue AS (
    SELECT
        c.month,
        COALESCE(SUM(o.delivery_fee) FILTER (WHERE o.status = 'Delivered'), 0) AS revenue
    FROM calendar AS c
    LEFT JOIN orders AS o
        ON date_trunc('month', o.order_date)::date = c.month
    GROUP BY c.month
)
SELECT
    month,
    revenue,
    SUM(revenue) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        AS running_revenue
FROM monthly_revenue
ORDER BY month;
