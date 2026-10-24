#!/usr/bin/env python3
"""YouTube Live Streaming API layer (uses client_secret.json in this folder).

Commands:
  auth <label>                     one-time browser consent for a channel account;
                                   saves token-<label>.json (label = e.g. mahakal)
  whoami <label>                   show which channel the token controls
  key <label> <stream-name>        get-or-create a reusable liveStream, print its
                                   RTMP key (put it in .env for that stream)
  go-live <label> <stream-name> <title>
                                   create a broadcast: public, auto-start,
                                   NO archive (recordFromStart=false), DVR off,
                                   bound to <stream-name>'s key. Start pushing the
                                   feed and it goes live with your dated title.
  retitle <label> <video-id> <title>
                                   rename a running broadcast (daily dated titles
                                   without interrupting the stream)
  meta <label> <video-id> <metadata.json> [audio credit]
                                   set title/description/tags/category from a
                                   metadata file ({date} and {audio_credit} are
                                   filled in), e.g. hanuman_chalisa/metadata.json
  thumbnail <label> <video-id> <image>
                                   upload a custom thumbnail (jpg/png, < 2 MB)
  cleanup <label>                  delete stray archived VODs of ended broadcasts

Typical setup per channel:
  python3 yt_api.py auth mahakal          # approve with the channel's account
  python3 yt_api.py key mahakal mahakal   # -> YT_KEY_MAHAKAL=... in .env
  python3 yt_api.py go-live mahakal mahakal "🔴 Mahakal Bhasma Aarti LIVE | 19 July 2026"
"""

import http.server
import json
import os
import socketserver
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET = os.path.join(HERE, "client_secret.json")
SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
API = "https://www.googleapis.com/youtube/v3/"


def _client():
    if not os.path.exists(CLIENT_SECRET):
        sys.exit("client_secret.json missing in pipeline folder")
    with open(CLIENT_SECRET) as f:
        return json.load(f)["installed"]


def _token_path(label):
    return os.path.join(HERE, f"token-{label}.json")


def _save_token(label, tok):
    tok["expires_at"] = time.time() + tok.get("expires_in", 3600)
    existing = {}
    if os.path.exists(_token_path(label)):
        with open(_token_path(label)) as f:
            existing = json.load(f)
    if "refresh_token" not in tok and "refresh_token" in existing:
        tok["refresh_token"] = existing["refresh_token"]
    with open(_token_path(label), "w") as f:
        json.dump(tok, f, indent=2)
    os.chmod(_token_path(label), 0o600)


def _post_form(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def _access_token(label):
    path = _token_path(label)
    if not os.path.exists(path):
        sys.exit(f"no token for '{label}' - run: yt_api.py auth {label}")
    with open(path) as f:
        tok = json.load(f)
    if time.time() > tok.get("expires_at", 0) - 60:
        c = _client()
        fresh = _post_form(c["token_uri"], {
            "client_id": c["client_id"], "client_secret": c["client_secret"],
            "refresh_token": tok["refresh_token"], "grant_type": "refresh_token"})
        _save_token(label, fresh)
        return fresh["access_token"]
    return tok["access_token"]


def _api(label, method, path, params=None, body=None):
    url = API + path + "?" + urllib.parse.urlencode(params or {})
    req = urllib.request.Request(
        url, data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {_access_token(label)}",
                 "Content-Type": "application/json"},
        method=method)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"API {method} {path} failed {e.code}: {e.read().decode()[:500]}")


def cmd_auth(label):
    c = _client()
    code_holder = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            code_holder["code"] = (q.get("code") or [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorized - you can close this tab.</h2>")

        def log_message(self, *a):
            pass

    port = 8765
    while True:
        try:
            httpd = socketserver.TCPServer(("127.0.0.1", port), H)
            break
        except OSError:
            port += 1
    redirect = f"http://localhost:{port}"
    url = c["auth_uri"] + "?" + urllib.parse.urlencode({
        "client_id": c["client_id"], "redirect_uri": redirect,
        "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent"})
    print("Open this URL and approve with the CHANNEL'S Google account:\n\n" + url + "\n")
    webbrowser.open(url)
    httpd.handle_request()
    httpd.server_close()
    if not code_holder.get("code"):
        sys.exit("no auth code received")
    tok = _post_form(c["token_uri"], {
        "client_id": c["client_id"], "client_secret": c["client_secret"],
        "code": code_holder["code"], "redirect_uri": redirect,
        "grant_type": "authorization_code"})
    _save_token(label, tok)
    print(f"token saved -> token-{label}.json")
    cmd_whoami(label)


def cmd_whoami(label):
    r = _api(label, "GET", "channels", {"part": "snippet,statistics", "mine": "true"})
    for it in r.get("items", []):
        print(f"channel: {it['snippet']['title']} ({it['id']}) - "
              f"{it['statistics'].get('subscriberCount', '?')} subs")


def _get_or_create_stream(label, name):
    r = _api(label, "GET", "liveStreams",
             {"part": "snippet,cdn", "mine": "true", "maxResults": "50"})
    for it in r.get("items", []):
        if it["snippet"]["title"] == name:
            return it
    return _api(label, "POST", "liveStreams",
                {"part": "snippet,cdn,contentDetails"},
                {"snippet": {"title": name},
                 "cdn": {"ingestionType": "rtmp", "resolution": "variable",
                         "frameRate": "variable"},
                 "contentDetails": {"isReusable": True}})


def cmd_key(label, name):
    s = _get_or_create_stream(label, name)
    ing = s["cdn"]["ingestionInfo"]
    env = "YT_KEY_" + name.upper().replace("-", "_")
    print(f"liveStream '{name}' (id {s['id']})")
    print(f"primary:  {ing['ingestionAddress']}")
    print(f"backup:   {ing.get('backupIngestionAddress', '-')}")
    print(f"\n{env}={ing['streamName']}")


def cmd_go_live(label, name, title):
    s = _get_or_create_stream(label, name)
    b = _api(label, "POST", "liveBroadcasts",
             {"part": "snippet,status,contentDetails"},
             {"snippet": {"title": title,
                          "scheduledStartTime":
                              time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              "status": {"privacyStatus": "public",
                         "selfDeclaredMadeForKids": False},
              "contentDetails": {"enableAutoStart": True, "enableAutoStop": False,
                                 "recordFromStart": False, "enableDvr": False,
                                 "monitorStream": {"enableMonitorStream": False}}})
    _api(label, "POST", "liveBroadcasts/bind",
         {"id": b["id"], "streamId": s["id"], "part": "id"})
    print(f"broadcast created (no-archive, auto-start): {title}")
    print(f"watch: https://youtube.com/watch?v={b['id']}")
    print("start pushing the feed to this stream's key and it goes live.")


def cmd_retitle(label, video_id, title):
    cur = _api(label, "GET", "videos", {"part": "snippet", "id": video_id})
    if not cur.get("items"):
        sys.exit("video not found")
    sn = cur["items"][0]["snippet"]
    sn["title"] = title
    _api(label, "PUT", "videos", {"part": "snippet"},
         {"id": video_id, "snippet": sn})
    print(f"retitled {video_id} -> {title}")


def cmd_meta(label, video_id, path, credit="-"):
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    fill = {"date": time.strftime("%d %B %Y"), "audio_credit": credit}
    cur = _api(label, "GET", "videos", {"part": "snippet", "id": video_id})
    if not cur.get("items"):
        sys.exit("video not found")
    sn = cur["items"][0]["snippet"]
    sn["title"] = m["title"].format(**fill)
    sn["description"] = m["description"].format(**fill)
    sn["tags"] = m["tags"]
    for k in ("categoryId", "defaultLanguage", "defaultAudioLanguage"):
        if k in m:
            sn[k] = m[k]
    _api(label, "PUT", "videos", {"part": "snippet"},
         {"id": video_id, "snippet": sn})
    print(f"metadata set on {video_id}: {sn['title']}")


def cmd_thumbnail(label, video_id, path):
    with open(path, "rb") as f:
        data = f.read()
    ctype = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/thumbnails/set?"
        + urllib.parse.urlencode({"videoId": video_id}),
        data=data, method="POST",
        headers={"Authorization": f"Bearer {_access_token(label)}",
                 "Content-Type": ctype})
    try:
        with urllib.request.urlopen(req) as r:
            r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"thumbnail upload failed {e.code}: {e.read().decode()[:500]}")
    print(f"thumbnail set on {video_id}")


def cmd_cleanup(label):
    r = _api(label, "GET", "liveBroadcasts",
             {"part": "id,status,snippet", "mine": "true", "maxResults": "50"})
    n = 0
    for it in r.get("items", []):
        if it["status"]["lifeCycleStatus"] == "complete":
            _api(label, "DELETE", "videos", {"id": it["id"]})
            print(f"deleted stray archive: {it['snippet']['title']} ({it['id']})")
            n += 1
    print(f"{n} stray archive(s) deleted")


if __name__ == "__main__":
    a = sys.argv
    try:
        if len(a) >= 3 and a[1] == "auth":
            cmd_auth(a[2])
        elif len(a) >= 3 and a[1] == "whoami":
            cmd_whoami(a[2])
        elif len(a) >= 4 and a[1] == "key":
            cmd_key(a[2], a[3])
        elif len(a) >= 5 and a[1] == "go-live":
            cmd_go_live(a[2], a[3], " ".join(a[4:]))
        elif len(a) >= 5 and a[1] == "retitle":
            cmd_retitle(a[2], a[3], " ".join(a[4:]))
        elif len(a) >= 5 and a[1] == "meta":
            cmd_meta(a[2], a[3], a[4], " ".join(a[5:]) or "-")
        elif len(a) >= 5 and a[1] == "thumbnail":
            cmd_thumbnail(a[2], a[3], a[4])
        elif len(a) >= 3 and a[1] == "cleanup":
            cmd_cleanup(a[2])
        else:
            sys.exit(__doc__)
    except KeyboardInterrupt:
        sys.exit(1)
