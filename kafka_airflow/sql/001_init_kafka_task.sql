CREATE SCHEMA IF NOT EXISTS kafka_prod;
CREATE SCHEMA IF NOT EXISTS kafka_dev;

CREATE TABLE IF NOT EXISTS kafka_prod.events_source (
    id BIGSERIAL PRIMARY KEY,
    user_name TEXT,
    email TEXT,
    age TEXT,
    site_action TEXT,
    event_date TEXT
);
