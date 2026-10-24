#!/usr/bin/env python3
"""Generate Hanuman ji artwork with G-Labs Studio (Meta Muse or Meta AI) and
drop it into the Shanivar special cover.

Runs on the machine where G-Labs Studio is open with its Webhook server started
(Webhook tab -> Start; MAX plan). Docs:
https://github.com/duckmartians/G-Labs-Studio/blob/main/WEBHOOK_INTEGRATION.en.md

Usage:
  set GLABS_API_KEY=<key from the Webhook tab>        (Windows)
  export GLABS_API_KEY=<key from the Webhook tab>     (Linux / macOS)

  python3 glabs_art.py                        # Meta Muse, 2 images, best one -> cover
  python3 glabs_art.py --engine meta          # Meta AI (vibes.ai) instead
  python3 glabs_art.py --count 4 --pick 3     # make 4, use the 3rd in the cover
  python3 glabs_art.py --prompt "..."         # your own prompt
  python3 glabs_art.py --no-cover             # only download the images

Images land in out/glabs/; the cover is rebuilt as out/cover.png + out/cover-thumb.jpg.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

PROMPT = (
    "Divine portrait of Lord Hanuman (Bajrangbali) in devotional Indian art style, "
    "facing the viewer with a calm, compassionate smile, hands folded in namaste, "
    "golden gada (mace) resting on his shoulder, saffron-orange body, ornate gold crown "
    "and jewellery, red dhoti, glowing golden halo behind his head, subtle 'Ram' "
    "inscriptions in the halo, warm sunrise rays, saffron and gold colour palette, "
    "centred composition with space around the head, highly detailed, soft cinematic "
    "lighting, serene and powerful, no text, no watermark"
)


def call(base, key, method, path, body=None):
    req = urllib.request.Request(
        base + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"X-API-Key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"G-Labs {method} {path} failed {e.code}: {e.read().decode()[:500]}")
    except urllib.error.URLError as e:
        sys.exit(f"cannot reach G-Labs at {base} ({e.reason}) - is the app open and "
                 "the Webhook server started?")


def submit(base, key, engine, prompt, count, ratio):
    if engine == "muse":
        return call(base, key, "POST", "/api/image/generate",
                    {"prompt": prompt, "model": "meta_muse", "mode": "text_to_image",
                     "aspect_ratio": ratio, "count": count})
    # Meta AI only knows 9:16, 16:9 and 1:1
    return call(base, key, "POST", "/api/meta/generate",
                {"prompt": prompt, "mode": "t2i", "count": count, "remove_logo": True,
                 "aspect_ratio": ratio if ratio in ("9:16", "16:9", "1:1") else "1:1"})


def wait(base, key, task_id, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = call(base, key, "GET", f"/api/status/{task_id}")
        if s["status"] == "completed":
            return s["results"]
        if s["status"] == "failed":
            sys.exit(f"generation failed [{s.get('error_code')}] {s.get('error')}")
        print(f"  {s['status']}...", flush=True)
        time.sleep(4)
    sys.exit(f"task {task_id} did not finish in {timeout}s")


def download(urls, outdir, task_id):
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for i, u in enumerate(urls, 1):
        ext = os.path.splitext(urllib.parse.urlparse(u).path)[1] or ".jpg"
        path = os.path.join(outdir, f"hanuman-{task_id}-{i}{ext}")
        with urllib.request.urlopen(u, timeout=120) as r, open(path, "wb") as f:
            f.write(r.read())
        paths.append(path)
        print(f"saved: {path}")
    return paths


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", choices=("muse", "meta"), default="muse")
    p.add_argument("--prompt", default=PROMPT)
    p.add_argument("--count", type=int, default=2, choices=(1, 2, 3, 4))
    p.add_argument("--ratio", default="1:1", help="1:1 fits the cover's round halo best")
    p.add_argument("--pick", type=int, default=1, help="which image (1-based) goes in the cover")
    p.add_argument("--base", default=os.environ.get("GLABS_URL", "http://127.0.0.1:8765"))
    p.add_argument("--timeout", type=int, default=1200)
    p.add_argument("--no-cover", action="store_true")
    a = p.parse_args()

    key = os.environ.get("GLABS_API_KEY")
    if not key:
        sys.exit("set GLABS_API_KEY to the key shown in G-Labs -> Webhook tab")
    base = a.base.rstrip("/")

    h = call(base, key, "GET", "/api/health")
    print(f"G-Labs: {h.get('status')} (running {h.get('tasks_running', 0)}, "
          f"pending {h.get('tasks_pending', 0)})")

    t = submit(base, key, a.engine, a.prompt, a.count, a.ratio)
    print(f"task {t['task_id']} queued on {'Meta Muse' if a.engine == 'muse' else 'Meta AI'}")
    paths = download(wait(base, key, t["task_id"], a.timeout),
                     os.path.join(HERE, "out", "glabs"), t["task_id"])

    if not a.no_cover:
        art = paths[min(max(a.pick, 1), len(paths)) - 1]
        subprocess.run([sys.executable, os.path.join(HERE, "make_cover.py"), "--image", art],
                       check=True)


if __name__ == "__main__":
    main()
