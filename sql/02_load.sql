-- Load the CSVs into the empty tables created by 01_schema.sql.
-- Run psql from the repository root so these relative paths resolve:
--   psql -v ON_ERROR_STOP=1 -d delivery_analytics -f sql/02_load.sql
-- Load order matters because of the foreign keys. Keep all five COPY operations
-- in one transaction so a bad row does not leave a half-loaded database.
BEGIN;

\copy kams (kam_id, kam_name, team) FROM 'data/kams.csv' WITH (FORMAT csv, HEADER true)
\copy hubs (hub_id, hub_name, district, division) FROM 'data/hubs.csv' WITH (FORMAT csv, HEADER true)
\copy merchants (merchant_id, merchant_name, category, onboarding_date, kam_id, tier) FROM 'data/merchants.csv' WITH (FORMAT csv, HEADER true)
\copy orders (order_id, merchant_id, hub_id, order_date, delivery_date, status, delivery_days, cod_amount, delivery_fee, cod_collected) FROM 'data/orders.csv' WITH (FORMAT csv, HEADER true)
\copy issues (issue_id, order_id, issue_type, opened_at, resolved_at, status) FROM 'data/issues.csv' WITH (FORMAT csv, HEADER true)

COMMIT;
