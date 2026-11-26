-- Flag merchants whose order count fell by more than 30% in the latest
-- three calendar months, compared with the three months before that.
WITH window_end AS (
    SELECT date_trunc('month', MAX(order_date)) + interval '1 month' AS next_month
    FROM orders
), merchant_volume AS (
    SELECT
        m.merchant_id,
        m.merchant_name,
        m.kam_id,
        COUNT(o.order_id) FILTER (
            WHERE o.order_date >= w.next_month - interval '6 months'
              AND o.order_date <  w.next_month - interval '3 months'
        ) AS previous_three_months,
        COUNT(o.order_id) FILTER (
            WHERE o.order_date >= w.next_month - interval '3 months'
              AND o.order_date <  w.next_month
        ) AS latest_three_months
    FROM merchants AS m
    CROSS JOIN window_end AS w
    LEFT JOIN orders AS o ON o.merchant_id = m.merchant_id
    GROUP BY m.merchant_id, m.merchant_name, m.kam_id
)
SELECT
    v.merchant_id,
    v.merchant_name,
    k.kam_name,
    v.previous_three_months,
    v.latest_three_months,
    ROUND(
        100.0 * (v.latest_three_months - v.previous_three_months)
        / NULLIF(v.previous_three_months, 0),
        1
    ) AS volume_change_pct
FROM merchant_volume AS v
JOIN kams AS k USING (kam_id)
WHERE v.previous_three_months >= 20
  AND v.latest_three_months < 0.70 * v.previous_three_months
ORDER BY volume_change_pct, v.merchant_id;
