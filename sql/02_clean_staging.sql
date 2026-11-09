-- Clean and type the raw rows, keeping one row per request.
-- If the API returned the same request twice, keep the most recently closed version.
CREATE OR REPLACE TEMP TABLE clean_requests AS
SELECT
    TRY_CAST(unique_key AS BIGINT) AS unique_key,
    TRY_CAST(created_date AS TIMESTAMP) AS created_at,
    TRY_CAST(closed_date AS TIMESTAMP) AS closed_at,
    UPPER(TRIM(agency)) AS agency_code,
    TRIM(agency_name) AS agency_name,
    TRIM(complaint_type) AS complaint_type,
    TRIM(descriptor) AS descriptor,
    TRIM(status) AS status,
    NULLIF(UPPER(TRIM(borough)), 'UNSPECIFIED') AS borough,
    LEFT(TRIM(incident_zip), 5) AS incident_zip,
    TRIM(open_data_channel_type) AS channel
FROM stg_service_requests
WHERE TRY_CAST(unique_key AS BIGINT) IS NOT NULL
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY TRY_CAST(unique_key AS BIGINT)
    ORDER BY TRY_CAST(closed_date AS TIMESTAMP) DESC NULLS LAST
) = 1;
