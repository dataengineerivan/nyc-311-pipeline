from datetime import datetime, timedelta
import requests
from config import API_URL, PAGE_SIZE

COLUMNS = [
    "unique_key", "created_date", "closed_date", "agency", "agency_name",
    "complaint_type", "descriptor", "status", "borough", "incident_zip",
    "open_data_channel_type",
]


def extract(since: datetime) -> list[dict]:
    """Pull every 311 request created on or after `since`, one page at a time."""
    rows, offset = [], 0
    where = f"created_date >= '{since:%Y-%m-%dT%H:%M:%S}'"
    while True:
        params = {
            "$select": ",".join(COLUMNS),
            "$where": where,
            "$order": "unique_key",
            "$limit": PAGE_SIZE,
            "$offset": offset,
        }
        resp = requests.get(API_URL, params=params, timeout=120)
        resp.raise_for_status()
        page = resp.json()
        rows.extend(page)
        print(f"  pulled {len(page):,} rows (offset {offset:,})")
        # a short page means we reached the end
        if len(page) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


def get_start_date(last_loaded, lookback_days, initial_days):
    """Decide where this run starts: a lookback window from the last load, or a first-run backfill."""
    midnight = dict(hour=0, minute=0, second=0, microsecond=0)
    if last_loaded is None:
        return (datetime.now() - timedelta(days=initial_days)).replace(**midnight)
    return (last_loaded - timedelta(days=lookback_days)).replace(**midnight)
