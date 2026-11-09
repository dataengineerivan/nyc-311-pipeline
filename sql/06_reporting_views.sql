-- Daily volume and resolution time by agency, ready for Power BI or Tableau
CREATE OR REPLACE VIEW vw_agency_daily_performance AS
SELECT
    d.full_date,
    d.day_of_week,
    a.agency_code,
    a.agency_name,
    COUNT(*) AS requests_created,
    COUNT(f.closed_at) AS requests_closed,
    ROUND(MEDIAN(f.resolution_hours), 1) AS median_resolution_hours,
    ROUND(AVG(f.resolution_hours), 1) AS avg_resolution_hours
FROM fact_service_request f
JOIN dim_date d ON d.date_key = f.created_date_key
LEFT JOIN dim_agency a ON a.agency_code = f.agency_code
GROUP BY ALL;

-- Top complaint types by channel (phone, online, mobile app)
CREATE OR REPLACE VIEW vw_complaints_by_channel AS
SELECT
    complaint_type,
    channel,
    COUNT(*) AS requests,
    ROUND(MEDIAN(resolution_hours), 1) AS median_resolution_hours
FROM fact_service_request
GROUP BY ALL;
