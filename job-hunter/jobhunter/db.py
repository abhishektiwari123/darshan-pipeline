import json
import sqlite3
from datetime import datetime, timezone

from .config import DATA

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    site TEXT,
    title TEXT,
    company TEXT,
    location TEXT,
    url TEXT,
    apply_url TEXT,
    ats TEXT,
    description TEXT,
    date_posted TEXT,
    score INTEGER,
    verdict TEXT,
    analysis TEXT,
    status TEXT DEFAULT 'new',
    notes TEXT,
    found_at TEXT,
    applied_at TEXT
)
"""

# new -> scored -> shortlisted | rejected -> applied | skipped | failed
STATUSES = ("new", "scored", "shortlisted", "rejected", "applied", "skipped", "failed")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATA / "jobs.db")
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def detect_ats(url: str) -> str:
    url = (url or "").lower()
    if "greenhouse.io" in url or "gh_jid=" in url:
        return "greenhouse"
    if "lever.co" in url:
        return "lever"
    if "ashbyhq.com" in url:
        return "ashby"
    if "linkedin.com" in url:
        return "linkedin"
    return "other"


def upsert(conn: sqlite3.Connection, job: dict) -> bool:
    """Insert a job if it is new. Returns True when inserted."""
    dup = conn.execute(
        "SELECT 1 FROM jobs WHERE id = ? OR url = ? OR (lower(company) = lower(?) AND lower(title) = lower(?))",
        (job["id"], job["url"], job["company"], job["title"]),
    ).fetchone()
    if dup:
        return False
    job.setdefault("ats", detect_ats(job.get("apply_url") or job["url"]))
    job["found_at"] = now()
    cols = ", ".join(job)
    conn.execute(
        f"INSERT INTO jobs ({cols}) VALUES ({', '.join('?' * len(job))})", list(job.values())
    )
    return True


def save_score(conn, job_id: str, score: int, verdict: str, analysis: dict, status: str):
    conn.execute(
        "UPDATE jobs SET score = ?, verdict = ?, analysis = ?, status = ? WHERE id = ?",
        (score, verdict, json.dumps(analysis), status, job_id),
    )
    conn.commit()


def set_status(conn, job_id: str, status: str, notes: str | None = None):
    if status not in STATUSES:
        raise SystemExit(f"Unknown status {status!r}. Use one of: {', '.join(STATUSES)}")
    applied_at = now() if status == "applied" else None
    conn.execute(
        "UPDATE jobs SET status = ?, notes = COALESCE(?, notes), applied_at = COALESCE(?, applied_at) WHERE id = ?",
        (status, notes, applied_at, job_id),
    )
    conn.commit()
