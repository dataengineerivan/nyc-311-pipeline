-- Landing table: raw text exactly as it came from the API, reloaded every run
CREATE TABLE IF NOT EXISTS stg_service_requests (
    unique_key VARCHAR,
    created_date VARCHAR,
    closed_date VARCHAR,
    agency VARCHAR,
    agency_name VARCHAR,
    complaint_type VARCHAR,
    descriptor VARCHAR,
    status VARCHAR,
    borough VARCHAR,
    incident_zip VARCHAR,
    open_data_channel_type VARCHAR
);

-- Dimension: one row per city agency
CREATE TABLE IF NOT EXISTS dim_agency (
    agency_code VARCHAR PRIMARY KEY,
    agency_name VARCHAR
);

-- Dimension: one row per complaint type
CREATE TABLE IF NOT EXISTS dim_complaint_type (
    complaint_type VARCHAR PRIMARY KEY,
    first_seen_date DATE
);

-- Dimension: one row per calendar day that appears in the data
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,   -- yyyymmdd
    full_date DATE,
    year INTEGER,
    month INTEGER,
    month_name VARCHAR,
    day_of_week VARCHAR,
    is_weekend BOOLEAN
);

-- Fact: one row per 311 service request
CREATE TABLE IF NOT EXISTS fact_service_request (
    unique_key BIGINT PRIMARY KEY,
    created_at TIMESTAMP,
    closed_at TIMESTAMP,
    created_date_key INTEGER,
    agency_code VARCHAR,
    complaint_type VARCHAR,
    descriptor VARCHAR,
    status VARCHAR,
    borough VARCHAR,
    incident_zip VARCHAR,
    channel VARCHAR,
    resolution_hours DOUBLE,
    loaded_at TIMESTAMP
);

-- Audit table: one row per pipeline run
CREATE TABLE IF NOT EXISTS pipeline_run_log (
    run_id INTEGER,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    window_start TIMESTAMP,
    rows_extracted INTEGER,
    rows_inserted INTEGER,
    rows_updated INTEGER,
    status VARCHAR,
    message VARCHAR
);
