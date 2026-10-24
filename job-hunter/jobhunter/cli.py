import argparse
import csv
import json

from . import config, db


def cmd_search(cfg, args):
    from .sources import discover

    discover(cfg)


def cmd_score(cfg, args):
    from .scorer import score_new

    score_new(cfg, args.limit)


def cmd_run(cfg, args):
    cmd_search(cfg, args)
    cmd_score(cfg, args)
    cmd_list(cfg, argparse.Namespace(status="shortlisted", limit=50))


def cmd_list(cfg, args):
    conn = db.connect()
    rows = conn.execute(
        "SELECT * FROM jobs WHERE (? IS NULL OR status = ?) ORDER BY score DESC NULLS LAST, found_at DESC LIMIT ?",
        (args.status, args.status, args.limit),
    ).fetchall()
    if not rows:
        print("No jobs yet.")
    for r in rows:
        score = "  -" if r["score"] is None else f"{r['score']:3d}"
        print(f"{score}  {r['status']:<11} {r['ats']:<10} {r['title'][:45]:<45}  {r['company'][:22]:<22}  {r['id']}")
        print(f"      {r['apply_url']}")
    counts = conn.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status").fetchall()
    print("\n" + ", ".join(f"{s}: {n}" for s, n in counts))


def cmd_show(cfg, args):
    row = db.connect().execute("SELECT * FROM jobs WHERE id = ?", (args.job_id,)).fetchone()
    if not row:
        raise SystemExit("No such job.")
    print(f"{row['title']} @ {row['company']} ({row['location']})\n{row['apply_url']}\nstatus: {row['status']}")
    if row["analysis"]:
        a = json.loads(row["analysis"])
        print(f"score {row['score']} ({row['verdict']}): {a.get('reason', '')}")
        print("matched: " + ", ".join(a.get("matched_skills", [])))
        print("gaps:    " + ", ".join(a.get("gaps", [])))


def cmd_apply(cfg, args):
    from .applier import apply_shortlisted

    if args.submit:
        cfg.setdefault("apply", {})["auto_submit"] = True
    apply_shortlisted(cfg, args.job_id, args.limit)


def cmd_mark(cfg, args):
    db.set_status(db.connect(), args.job_id, args.status, args.note)
    print(f"{args.job_id} -> {args.status}")


def cmd_export(cfg, args):
    rows = db.connect().execute("SELECT * FROM jobs ORDER BY score DESC NULLS LAST").fetchall()
    out = config.DATA / "jobs.csv"
    cols = ["score", "status", "title", "company", "location", "ats", "apply_url", "verdict", "applied_at", "notes", "id"]
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(cols + ["reason"])
        for r in rows:
            reason = json.loads(r["analysis"]).get("reason", "") if r["analysis"] else ""
            writer.writerow([r[c] for c in cols] + [reason])
    print(f"Wrote {len(rows)} jobs to {out}")


def main():
    parser = argparse.ArgumentParser(prog="jobhunter", description="Find, shortlist and apply to jobs.")
    parser.add_argument("--config", help="path to config.yaml (default: ./config.yaml)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("search", help="find new jobs from job boards and company boards")
    p = sub.add_parser("score", help="score new jobs against your resume with Claude")
    p.add_argument("--limit", type=int)
    p = sub.add_parser("run", help="search + score + show the shortlist")
    p.add_argument("--limit", type=int, help="max jobs to score this run")
    p = sub.add_parser("list", help="list jobs")
    p.add_argument("--status", choices=db.STATUSES)
    p.add_argument("--limit", type=int, default=50)
    p = sub.add_parser("show", help="show one job and why it was scored that way")
    p.add_argument("job_id")
    p = sub.add_parser("apply", help="fill in applications for shortlisted jobs")
    p.add_argument("--job-id", help="apply to one job (any status)")
    p.add_argument("--limit", type=int)
    p.add_argument("--submit", action="store_true", help="click Submit automatically on Greenhouse/Lever/Ashby forms")
    p = sub.add_parser("mark", help="set a job's status by hand")
    p.add_argument("job_id")
    p.add_argument("status", choices=db.STATUSES)
    p.add_argument("--note")
    sub.add_parser("export", help="write all jobs to data/jobs.csv")

    args = parser.parse_args()
    cfg = config.load(args.config)
    globals()[f"cmd_{args.command}"](cfg, args)
