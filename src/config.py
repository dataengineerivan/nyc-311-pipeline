from pathlib import Path

# NYC Open Data: 311 Service Requests from 2010 to Present (free, no API key needed)
API_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"

# How many days back to re-pull on every run.
# 311 requests get updated after they are created (closed, status changes),
# so re-pulling a recent window and upserting keeps the warehouse current.
LOOKBACK_DAYS = 7

# First run only: how many days of history to load
INITIAL_DAYS = 30

PAGE_SIZE = 50000

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "nyc311.duckdb"
SQL_DIR = ROOT / "sql"
