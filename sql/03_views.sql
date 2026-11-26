-- Reporting views used by the example queries and the Power BI model.

CREATE OR REPLACE VIEW vw_dim_kam AS
SELECT kam_id, kam_name, team
FROM kams;

CREATE OR REPLACE VIEW vw_dim_merchant AS
SELECT merchant_id, merchant_name, category, onboarding_date, kam_id, tier
FROM merchants;

CREATE OR REPLACE VIEW vw_dim_hub AS
SELECT hub_id, hub_name, district, division
FROM hubs;

CREATE OR REPLACE VIEW vw_fact_orders AS
SELECT
    o.order_id,
    o.order_date,
    o.delivery_date,
    o.merchant_id,
    o.hub_id,
    m.kam_id,
    o.status,
    o.delivery_days,
    o.cod_amount,
    o.delivery_fee,
    o.cod_collected,
    (o.status = 'Delivered')::integer AS delivered_order,
    (o.status = 'Returned')::integer AS returned_order,
    (o.status = 'Failed')::integer AS failed_order,
    CASE WHEN o.status = 'Delivered' THEN o.delivery_fee ELSE 0 END AS recognized_revenue
FROM orders AS o
JOIN merchants AS m USING (merchant_id);

CREATE OR REPLACE VIEW vw_fact_issues AS
SELECT
    i.issue_id,
    i.order_id,
    i.issue_type,
    i.opened_at,
    i.opened_at::date AS opened_date,
    i.resolved_at,
    i.status,
    o.order_date,
    o.merchant_id,
    o.hub_id,
    m.kam_id,
    CASE
        WHEN i.resolved_at IS NOT NULL
        THEN EXTRACT(EPOCH FROM (i.resolved_at - i.opened_at)) / 3600.0
    END AS resolution_hours
FROM issues AS i
JOIN orders AS o USING (order_id)
JOIN merchants AS m USING (merchant_id);

CREATE OR REPLACE VIEW vw_monthly_delivery_metrics AS
SELECT
    date_trunc('month', order_date)::date AS month,
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'Delivered') AS delivered_orders,
    COUNT(*) FILTER (WHERE status = 'Returned') AS returned_orders,
    COUNT(*) FILTER (WHERE status = 'Failed') AS failed_orders,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'Delivered') / NULLIF(COUNT(*), 0),
        2
    ) AS delivery_success_rate_pct,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'Returned') / NULLIF(COUNT(*), 0),
        2
    ) AS return_rate_pct,
    ROUND(AVG(delivery_days), 2) AS average_delivery_days,
    COUNT(*) FILTER (WHERE status = 'Delivered' AND cod_amount > 0) AS delivered_cod_orders,
    COUNT(*) FILTER (WHERE status = 'Delivered' AND cod_amount > 0 AND cod_collected = 1)
        AS collected_cod_orders,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'Delivered' AND cod_amount > 0 AND cod_collected = 1)
        / NULLIF(COUNT(*) FILTER (WHERE status = 'Delivered' AND cod_amount > 0), 0),
        2
    ) AS cod_collection_rate_pct,
    SUM(delivery_fee) FILTER (WHERE status = 'Delivered') AS recognized_revenue
FROM orders
GROUP BY date_trunc('month', order_date)::date;
