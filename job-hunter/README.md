# Job Hunter

A command-line tool that **finds jobs, shortlists the ones that fit you, and fills in the applications**.

1. **Search**: pulls new postings from LinkedIn, Indeed, Naukri, Glassdoor and Google Jobs (via [JobSpy](https://github.com/speedyapply/JobSpy)), plus the Greenhouse, Lever and Ashby job boards of companies you name.
2. **Shortlist**: Claude reads each posting next to your resume and preferences and gives it a 0–100 score with matched skills, gaps and a one-line reason. Jobs at or above your threshold are shortlisted.
3. **Apply**: opens each shortlisted job in a browser, fills in your details, uploads your resume, and has Claude answer the form's other questions (dropdowns, yes/no, "why this company", cover letters) from your resume and saved answers. You review and press Submit, or turn on auto-submit.

Everything is stored in a local SQLite database (`data/jobs.db`), so each run only handles new jobs and nothing is applied to twice.

## Setup

```bash
cd job-hunter
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

export ANTHROPIC_API_KEY=sk-ant-...      # from console.anthropic.com

cp config.example.yaml config.yaml       # then edit it
cp ~/path/to/your-resume.pdf resume.pdf
```

In `config.yaml`, fill in your profile, preferences, search terms and locations. Optionally:
- Add a plain-text copy of your resume as `resume.md`. Scoring is cheaper and more accurate than with the PDF alone.
- List target companies under `companies:`. Their Greenhouse, Lever and Ashby boards give the most reliable form-filling.

`config.yaml`, `resume.*` and `data/` are git-ignored.

## Daily use

```bash
python -m jobhunter run              # search + score + print the shortlist
python -m jobhunter apply            # fill in applications for the shortlist, best scores first
```

Other commands:

| Command | What it does |
|---|---|
| `search` | Find new jobs only |
| `score [--limit N]` | Score jobs not yet scored |
| `list [--status shortlisted]` | Show jobs with score, status and apply link |
| `show <job-id>` | Why a job got its score (matched skills, gaps) |
| `apply --job-id <id>` | Apply to one specific job |
| `apply --submit` | Click Submit automatically (Greenhouse / Lever / Ashby only) |
| `mark <job-id> applied\|skipped\|rejected` | Update a job by hand |
| `export` | Write every job to `data/jobs.csv` |

## How applying works

- The browser opens in a window (`headless: false`) so you can watch it. It uses a saved browser profile in `data/browser-profile`, so if a site needs a login, log in once and it stays logged in.
- Name, email, phone, LinkedIn and similar fields come straight from your profile. Every other field goes to Claude, which may only use facts from your resume, profile and `answers:`. If it doesn't know something (salary, notice period, and so on), it leaves the field empty and tells you which one. Add those to `answers:` so they're filled next time.
- With `auto_submit: false` (the default), you review each filled form, submit it yourself, then answer `y` in the terminal to record it as applied.
- With `auto_submit: true` / `--submit`, it clicks Submit only on Greenhouse, Lever and Ashby forms, only when no field needed your input, and only records the job as applied when it sees a confirmation message. Every other form still waits for you.
- A screenshot of each filled form is saved in `data/screenshots/`.
- **LinkedIn applications are never automated.** LinkedIn restricts accounts that use bots. LinkedIn jobs are found and scored, and the `apply` step prints their links for you to apply by hand. Many LinkedIn postings link to the company's own Greenhouse or Lever page, and those are filled in normally.
- CAPTCHAs are not bypassed. If one appears, solve it in the window and submit.

## Cost

Scoring uses `claude-opus-5-5` at `low` effort by default. Your resume is prompt-cached, so it's billed in full only once per run, plus a small amount per posting. Expect about a cent or two per job scored, plus a few cents per application filled. Change `scoring.model` / `scoring.effort` in the config to trade cost against quality.

## Tips

- Keep `shortlist_min_score` at 70 or higher. A few strong, tailored applications usually beat a flood of weak ones.
- Run `show <id>` on a few rejected jobs at first. If the scoring looks off, sharpen the `preferences` text.
- Job boards change their pages and rate-limit scrapers. If one site stops returning results, the others keep working.
