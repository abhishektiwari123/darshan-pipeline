"""Job discovery: JobSpy (LinkedIn, Indeed, Naukri, ...) plus company boards on Greenhouse, Lever and Ashby."""

import hashlib
import html
import json
import re
import urllib.request

from . import db


def _id(prefix: str, value: str) -> str:
    return f"{prefix}:{hashlib.sha1(value.encode()).hexdigest()[:12]}"


def _clean(value) -> str:
    if value is None or (isinstance(value, float) and value != value):  # NaN from pandas
        return ""
    return str(value)


def _strip_html(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "job-hunter/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _title_ok(title: str, search: dict) -> bool:
    t = title.lower()
    must = [w.lower() for w in search.get("title_must_include") or []]
    if must and not any(w in t for w in must):
        return False
    return not any(w.lower() in t for w in search.get("title_exclude") or [])


def from_jobspy(search: dict) -> list[dict]:
    from jobspy import scrape_jobs

    jobs = []
    for term in search.get("terms", []):
        for location in search.get("locations", [""]):
            print(f"  searching {search['sites']} for {term!r} in {location or 'anywhere'}")
            try:
                df = scrape_jobs(
                    site_name=search["sites"],
                    search_term=term,
                    google_search_term=f"{term} jobs near {location}" if location else term,
                    location=location or None,
                    results_wanted=search.get("results_per_search", 25),
                    hours_old=search.get("hours_old"),
                    is_remote=search.get("is_remote", False),
                    country_indeed=search.get("country_indeed", "usa"),
                    linkedin_fetch_description=True,
                    verbose=0,
                )
            except Exception as exc:  # one failing site must not stop the run
                print(f"    failed: {exc}")
                continue
            for row in df.to_dict("records"):
                url = _clean(row.get("job_url"))
                if not url:
                    continue
                direct = _clean(row.get("job_url_direct"))
                jobs.append({
                    "id": _id(_clean(row.get("site")) or "web", url),
                    "site": _clean(row.get("site")),
                    "title": _clean(row.get("title")),
                    "company": _clean(row.get("company")),
                    "location": _clean(row.get("location")),
                    "url": url,
                    "apply_url": direct or url,
                    "description": _clean(row.get("description")),
                    "date_posted": _clean(row.get("date_posted")),
                })
    return jobs


def from_greenhouse(slug: str) -> list[dict]:
    data = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
    return [{
        "id": f"greenhouse:{slug}:{j['id']}",
        "site": "greenhouse",
        "title": j.get("title", ""),
        "company": slug,
        "location": (j.get("location") or {}).get("name", ""),
        "url": j["absolute_url"],
        "apply_url": j["absolute_url"],
        "ats": "greenhouse",
        "description": _strip_html(j.get("content", "")),
        "date_posted": j.get("updated_at", ""),
    } for j in data.get("jobs", [])]


def from_lever(slug: str) -> list[dict]:
    data = _get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    return [{
        "id": f"lever:{slug}:{j['id']}",
        "site": "lever",
        "title": j.get("text", ""),
        "company": slug,
        "location": (j.get("categories") or {}).get("location", ""),
        "url": j["hostedUrl"],
        "apply_url": j.get("applyUrl") or j["hostedUrl"] + "/apply",
        "ats": "lever",
        "description": j.get("descriptionPlain", "") + "\n\n" + "\n".join(
            f"{block.get('text', '')}\n{_strip_html(block.get('content', ''))}" for block in j.get("lists", [])
        ),
        "date_posted": str(j.get("createdAt", "")),
    } for j in data]


def from_ashby(slug: str) -> list[dict]:
    data = _get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    return [{
        "id": f"ashby:{slug}:{j.get('id') or j['jobUrl']}",
        "site": "ashby",
        "title": j.get("title", ""),
        "company": slug,
        "location": j.get("location", "") + (" (remote)" if j.get("isRemote") else ""),
        "url": j["jobUrl"],
        "apply_url": j.get("applyUrl") or j["jobUrl"] + "/application",
        "ats": "ashby",
        "description": j.get("descriptionPlain") or _strip_html(j.get("descriptionHtml", "")),
        "date_posted": j.get("publishedAt", ""),
    } for j in data.get("jobs", [])]


BOARDS = {"greenhouse": from_greenhouse, "lever": from_lever, "ashby": from_ashby}


def from_company_boards(companies: dict, search: dict) -> list[dict]:
    wanted = [w.lower() for w in companies.get("location_filter") or []]
    jobs = []
    for ats, fetch in BOARDS.items():
        for slug in companies.get(ats) or []:
            print(f"  reading {ats} board {slug!r}")
            try:
                board = fetch(slug)
            except Exception as exc:
                print(f"    failed: {exc}")
                continue
            for job in board:
                if wanted and not any(w in job["location"].lower() for w in wanted):
                    continue
                jobs.append(job)
    return jobs


def discover(cfg: dict) -> int:
    search = cfg.get("search", {})
    found = []
    if search.get("sites") and search.get("terms"):
        found += from_jobspy(search)
    found += from_company_boards(cfg.get("companies") or {}, search)

    conn = db.connect()
    added = sum(db.upsert(conn, job) for job in found if job["title"] and _title_ok(job["title"], search))
    conn.commit()
    print(f"Found {len(found)} jobs, {added} new after filters and de-duplication.")
    return added
