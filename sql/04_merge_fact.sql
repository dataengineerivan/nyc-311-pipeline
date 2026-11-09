-- Upsert into the fact table:
--   new requests get inserted, existing requests get updated only when something changed
--   (most often a request getting closed). Re-running the same window changes nothing.
MERGE INTO fact_service_request f
USING (
    SELECT
        *,
        CAST(strftime(created_at, '%Y%m%d') AS INTEGER) AS created_date_key,
        -- only count resolution time when the close date makes sense
        CASE WHEN closed_at >= created_at
             THEN date_diff('minute', created_at, closed_at) / 60.0 END AS resolution_hours
    FROM clean_requests
) s
ON f.unique_key = s.unique_key
WHEN MATCHED AND (
       f.status IS DISTINCT FROM s.status
    OR f.closed_at IS DISTINCT FROM s.closed_at
    OR f.descriptor IS DISTINCT FROM s.descriptor
) THEN UPDATE SET
    status = s.status,
    closed_at = s.closed_at,
    descriptor = s.descriptor,
    resolution_hours = s.resolution_hours,
    loaded_at = current_timestamp
WHEN NOT MATCHED THEN INSERT (
    unique_key, created_at, closed_at, created_date_key, agency_code, complaint_type,
    descriptor, status, borough, incident_zip, channel, resolution_hours, loaded_at
) VALUES (
    s.unique_key, s.created_at, s.closed_at, s.created_date_key, s.agency_code, s.complaint_type,
    s.descriptor, s.status, s.borough, s.incident_zip, s.channel, s.resolution_hours, current_timestamp
);
