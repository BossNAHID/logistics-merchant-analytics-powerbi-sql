-- Volume and service level by hub. Success/return rates use all orders
-- assigned to the hub as their denominator.
SELECT
    h.hub_id,
    h.hub_name,
    h.district,
    h.division,
    COUNT(o.order_id) AS total_orders,
    COUNT(*) FILTER (WHERE o.status = 'Delivered') AS delivered_orders,
    COUNT(*) FILTER (WHERE o.status = 'Returned') AS returned_orders,
    COUNT(*) FILTER (WHERE o.status = 'Failed') AS failed_orders,
    ROUND(100.0 * COUNT(*) FILTER (WHERE o.status = 'Delivered') / NULLIF(COUNT(*), 0), 2)
        AS delivery_success_rate_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE o.status = 'Returned') / NULLIF(COUNT(*), 0), 2)
        AS return_rate_pct,
    ROUND(AVG(o.delivery_days), 2) AS average_delivery_days
FROM hubs AS h
JOIN orders AS o USING (hub_id)
GROUP BY h.hub_id, h.hub_name, h.district, h.division
ORDER BY average_delivery_days DESC, total_orders DESC;
