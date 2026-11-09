"""
NYC 311 incremental pipeline: API -> staging -> star schema in DuckDB.

Run:  python src/pipeline.py
"""
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import duckdb

from config import DB_PATH, SQL_DIR, LOOKBACK_DAYS, INITIAL_DAYS
from extract import extract, get_start_date, COLUMNS


def run_sql_file(con, name):
    con.execute((SQL_DIR / name).read_text())


def load_staging(con, rows):
    """Write the API rows to a temp file and bulk load them into the staging table."""
    con.execute("DELETE FROM stg_service_requests")
    if not rows:
        return
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        for r in rows:
            # keep only the columns we expect, as text, so the load never breaks on a new field
            f.write(json.dumps({c: (None if r.get(c) is None else str(r.get(c))) for c in COLUMNS}) + "\n")
        path = f.name
    cols = ", ".join(f"'{c}': 'VARCHAR'" for c in COLUMNS)
    con.execute(f"INSERT INTO stg_service_requests SELECT * FROM read_json('{path}', format='newline_delimited', columns={{{cols}}})")
    Path(path).unlink()


def run(con, fetch=extract):
    started = datetime.now()
    run_sql_file(con, "01_create_tables.sql")
    run_id = con.execute("SELECT COALESCE(MAX(run_id), 0) + 1 FROM pipeline_run_log").fetchone()[0]

    last_loaded = con.execute("SELECT MAX(created_at) FROM fact_service_request").fetchone()[0]
    window_start = get_start_date(last_loaded, LOOKBACK_DAYS, INITIAL_DAYS)
    print(f"Run {run_id}: pulling requests created since {window_start:%Y-%m-%d}")

    inserted = updated = 0
    rows = []
    try:
        rows = fetch(window_start)
        con.execute("BEGIN TRANSACTION")
        load_staging(con, rows)
        run_sql_file(con, "02_clean_staging.sql")

        # count new vs existing keys before the merge so the log shows what changed
        before = con.execute("SELECT COUNT(*) FROM fact_service_request").fetchone()[0]
        changed = con.execute("""
            SELECT COUNT(*) FROM clean_requests s JOIN fact_service_request f USING (unique_key)
            WHERE f.status IS DISTINCT FROM s.status
               OR f.closed_at IS DISTINCT FROM s.closed_at
               OR f.descriptor IS DISTINCT FROM s.descriptor
        """).fetchone()[0]

        run_sql_file(con, "03_load_dimensions.sql")
        run_sql_file(con, "04_merge_fact.sql")
        inserted = con.execute("SELECT COUNT(*) FROM fact_service_request").fetchone()[0] - before
        updated = changed

        checks = con.execute((SQL_DIR / "05_quality_checks.sql").read_text()).fetchall()
        for name, severity, failed in checks:
            if failed:
                print(f"  [{severity}] {name}: {failed:,} rows")
        errors = [c for c in checks if c[1] == "error" and c[2] > 0]
        if errors:
            raise ValueError(f"Quality check failed: {errors[0][0]}")

        run_sql_file(con, "06_reporting_views.sql")
        con.execute("COMMIT")
        status, message = "success", ""
    except Exception as e:
        # roll back so a bad run never leaves half-loaded data behind
        try:
            con.execute("ROLLBACK")
        except duckdb.Error:
            pass
        status, message, inserted, updated = "failed", str(e)[:500], 0, 0

    con.execute(
        "INSERT INTO pipeline_run_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [run_id, started, datetime.now(), window_start, len(rows), inserted, updated, status, message],
    )
    print(f"Run {run_id} {status}: {len(rows):,} extracted, {inserted:,} inserted, {updated:,} updated")
    return status


if __name__ == "__main__":
    DB_PATH.parent.mkdir(exist_ok=True)
    with duckdb.connect(str(DB_PATH)) as con:
        sys.exit(0 if run(con) == "success" else 1)
