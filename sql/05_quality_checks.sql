-- Each check returns how many rows fail it. Severity "error" stops the run; "warning" is logged.
SELECT 'fact rows missing created date' AS check_name, 'error' AS severity, COUNT(*) AS failed_rows
FROM fact_service_request WHERE created_at IS NULL
UNION ALL
SELECT 'fact rows with unknown agency', 'error', COUNT(*)
FROM fact_service_request f
WHERE f.agency_code IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM dim_agency a WHERE a.agency_code = f.agency_code)
UNION ALL
SELECT 'closed before created', 'warning', COUNT(*)
FROM fact_service_request WHERE closed_at < created_at
UNION ALL
SELECT 'created in the future', 'warning', COUNT(*)
FROM fact_service_request WHERE created_at > current_timestamp + INTERVAL 1 DAY
UNION ALL
SELECT 'missing borough', 'warning', COUNT(*)
FROM fact_service_request WHERE borough IS NULL;
