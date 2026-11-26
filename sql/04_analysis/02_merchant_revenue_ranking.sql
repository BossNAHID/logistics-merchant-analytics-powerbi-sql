-- Delivery revenue is the delivery fee on completed deliveries.
-- COD is collected for the merchant and is not counted as courier revenue.
WITH merchant_revenue AS (
    SELECT
        m.merchant_id,
        m.merchant_name,
        k.kam_name,
        m.category,
        COUNT(o.order_id) AS delivered_orders,
        COALESCE(SUM(o.delivery_fee), 0) AS recognized_revenue
    FROM merchants AS m
    JOIN kams AS k USING (kam_id)
    LEFT JOIN orders AS o
        ON o.merchant_id = m.merchant_id
       AND o.status = 'Delivered'
    GROUP BY m.merchant_id, m.merchant_name, k.kam_name, m.category
), ranked AS (
    SELECT
        *,
        RANK() OVER (ORDER BY recognized_revenue DESC) AS revenue_rank,
        NTILE(10) OVER (ORDER BY recognized_revenue DESC) AS revenue_decile
    FROM merchant_revenue
)
SELECT *
FROM ranked
ORDER BY revenue_rank, merchant_id;
