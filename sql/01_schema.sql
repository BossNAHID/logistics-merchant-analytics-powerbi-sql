-- PostgreSQL schema for the synthetic delivery-analytics project.
-- Create a fresh database before running this file; it deliberately does not drop data.

CREATE TABLE kams (
    kam_id   varchar(5) PRIMARY KEY,
    kam_name varchar(80) NOT NULL,
    team     varchar(40) NOT NULL
);

CREATE TABLE hubs (
    hub_id   varchar(5) PRIMARY KEY,
    hub_name varchar(80) NOT NULL,
    district varchar(60) NOT NULL,
    division varchar(60) NOT NULL
);

CREATE TABLE merchants (
    merchant_id     varchar(8) PRIMARY KEY,
    merchant_name   varchar(100) NOT NULL,
    category        varchar(60) NOT NULL,
    onboarding_date date NOT NULL,
    kam_id          varchar(5) NOT NULL REFERENCES kams (kam_id),
    tier            varchar(20) NOT NULL CHECK (tier IN ('Silver', 'Gold', 'Platinum'))
);

CREATE TABLE orders (
    order_id      varchar(12) PRIMARY KEY,
    merchant_id   varchar(8) NOT NULL REFERENCES merchants (merchant_id),
    hub_id        varchar(5) NOT NULL REFERENCES hubs (hub_id),
    order_date    date NOT NULL,
    delivery_date date,
    status        varchar(20) NOT NULL
                  CHECK (status IN ('Delivered', 'Returned', 'Failed', 'Cancelled')),
    delivery_days smallint CHECK (delivery_days BETWEEN 1 AND 12),
    cod_amount    integer NOT NULL CHECK (cod_amount >= 0),
    delivery_fee  integer NOT NULL CHECK (delivery_fee >= 0),
    cod_collected smallint NOT NULL CHECK (cod_collected IN (0, 1)),
    CHECK (
        (status = 'Cancelled' AND delivery_date IS NULL AND delivery_days IS NULL)
        OR
        (status <> 'Cancelled' AND delivery_date IS NOT NULL AND delivery_days IS NOT NULL)
    ),
    CHECK (cod_collected = 0 OR (status = 'Delivered' AND cod_amount > 0))
);

CREATE TABLE issues (
    issue_id    varchar(10) PRIMARY KEY,
    order_id    varchar(12) NOT NULL REFERENCES orders (order_id),
    issue_type  varchar(40) NOT NULL,
    opened_at   timestamp NOT NULL,
    resolved_at timestamp,
    status      varchar(12) NOT NULL CHECK (status IN ('Open', 'Resolved')),
    CHECK (
        (status = 'Open' AND resolved_at IS NULL)
        OR
        (status = 'Resolved' AND resolved_at IS NOT NULL)
    ),
    CHECK (resolved_at IS NULL OR resolved_at >= opened_at)
);

CREATE INDEX idx_merchants_kam       ON merchants (kam_id);
CREATE INDEX idx_orders_order_date   ON orders (order_date);
CREATE INDEX idx_orders_merchant_day ON orders (merchant_id, order_date);
CREATE INDEX idx_orders_hub_day      ON orders (hub_id, order_date);
CREATE INDEX idx_issues_order        ON issues (order_id);
CREATE INDEX idx_issues_status_type  ON issues (status, issue_type);
