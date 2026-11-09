-- Add new agencies; refresh the name if the city renamed one
MERGE INTO dim_agency d
USING (SELECT agency_code, MAX(agency_name) AS agency_name
       FROM clean_requests WHERE agency_code IS NOT NULL GROUP BY agency_code) s
ON d.agency_code = s.agency_code
WHEN MATCHED AND d.agency_name IS DISTINCT FROM s.agency_name THEN UPDATE SET agency_name = s.agency_name
WHEN NOT MATCHED THEN INSERT (agency_code, agency_name) VALUES (s.agency_code, s.agency_name);

-- Add complaint types we have not seen before
INSERT INTO dim_complaint_type (complaint_type, first_seen_date)
SELECT complaint_type, MIN(CAST(created_at AS DATE))
FROM clean_requests
WHERE complaint_type IS NOT NULL
  AND complaint_type NOT IN (SELECT complaint_type FROM dim_complaint_type)
GROUP BY complaint_type;

-- Add any calendar days we have not seen before
INSERT INTO dim_date
SELECT DISTINCT
    CAST(strftime(created_at, '%Y%m%d') AS INTEGER),
    CAST(created_at AS DATE),
    year(created_at),
    month(created_at),
    monthname(created_at),
    dayname(created_at),
    dayofweek(created_at) IN (0, 6)
FROM clean_requests
WHERE created_at IS NOT NULL
  AND CAST(strftime(created_at, '%Y%m%d') AS INTEGER) NOT IN (SELECT date_key FROM dim_date);
