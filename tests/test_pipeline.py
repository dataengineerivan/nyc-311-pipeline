"""Tests run fully offline: the API call is replaced with sample rows shaped like the real API."""
import duckdb
from pipeline import run


AGENCY_NAMES = {"NYPD": "New York City Police Department", "DSNY": "Department of Sanitation"}


def make_row(key, created, closed=None, status="Open", agency="NYPD", complaint="Noise - Residential"):
    return {
        "unique_key": str(key), "created_date": created, "closed_date": closed,
        "agency": agency, "agency_name": AGENCY_NAMES[agency],
        "complaint_type": complaint, "descriptor": "Loud Music/Party", "status": status,
        "borough": "BROOKLYN", "incident_zip": "11201", "open_data_channel_type": "PHONE",
    }


FIRST_LOAD = [
    make_row(1, "2026-10-01T22:15:00.000"),
    make_row(2, "2026-10-02T08:00:00.000", "2026-10-02T10:30:00.000", "Closed"),
    make_row(2, "2026-10-02T08:00:00.000", "2026-10-02T10:30:00.000", "Closed"),  # duplicate from the API
    make_row(3, "2026-10-03T09:00:00.000", agency="DSNY", complaint="Missed Collection"),
]


def fake_fetch(rows):
    return lambda since: rows


def test_first_load_builds_star_schema():
    con = duckdb.connect()
    assert run(con, fake_fetch(FIRST_LOAD)) == "success"
    assert con.execute("SELECT COUNT(*) FROM fact_service_request").fetchone()[0] == 3
    assert con.execute("SELECT COUNT(*) FROM dim_agency").fetchone()[0] == 2
    assert con.execute("SELECT COUNT(*) FROM dim_date").fetchone()[0] == 3
    hours = con.execute("SELECT resolution_hours FROM fact_service_request WHERE unique_key = 2").fetchone()[0]
    assert hours == 2.5


def test_rerun_is_idempotent():
    con = duckdb.connect()
    run(con, fake_fetch(FIRST_LOAD))
    run(con, fake_fetch(FIRST_LOAD))
    assert con.execute("SELECT COUNT(*) FROM fact_service_request").fetchone()[0] == 3
    log = con.execute("SELECT rows_inserted, rows_updated FROM pipeline_run_log WHERE run_id = 2").fetchone()
    assert log == (0, 0)


def test_closed_request_gets_updated():
    con = duckdb.connect()
    run(con, fake_fetch(FIRST_LOAD))
    later = [make_row(1, "2026-10-01T22:15:00.000", "2026-10-02T01:15:00.000", "Closed")]
    run(con, fake_fetch(later))
    status, hours = con.execute(
        "SELECT status, resolution_hours FROM fact_service_request WHERE unique_key = 1").fetchone()
    assert (status, hours) == ("Closed", 3.0)
    assert con.execute("SELECT rows_updated FROM pipeline_run_log WHERE run_id = 2").fetchone()[0] == 1


def test_bad_close_date_is_not_counted():
    con = duckdb.connect()
    bad = [make_row(9, "2026-10-05T12:00:00.000", "2026-10-04T12:00:00.000", "Closed")]
    run(con, fake_fetch(bad))
    assert con.execute("SELECT resolution_hours FROM fact_service_request").fetchone()[0] is None


def test_failed_run_leaves_no_partial_data():
    con = duckdb.connect()
    def broken(since):
        raise ConnectionError("API down")
    assert run(con, broken) == "failed"
    assert con.execute("SELECT COUNT(*) FROM fact_service_request").fetchone()[0] == 0
    assert con.execute("SELECT status FROM pipeline_run_log").fetchone()[0] == "failed"
