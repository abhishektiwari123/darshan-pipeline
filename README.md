# Darshan Pipeline

A small, private command-line tool that manages **live broadcasts on YouTube channels owned by its operator**, via the official YouTube Data API v3 (Live Streaming). It exists to run daily devotional (temple darshan / aarti) live streams reliably: creating scheduled broadcasts with dated titles, binding them to reusable stream keys, and cleaning up ended broadcasts.

> **Scope:** This tool only ever operates on channels the operator owns, after an explicit OAuth 2.0 consent. It has no public interface, no server component, and no access to any other user's data. It is not affiliated with, endorsed by, or sponsored by YouTube or Google.

## What it does

| Command | Purpose |
|---|---|
| `auth <label>` | One-time OAuth consent for a channel account (tokens stored locally) |
| `whoami <label>` | Show which channel a stored token controls |
| `key <label> <stream-name>` | Get or create a reusable live stream, print its RTMP ingestion key |
| `go-live <label> <stream-name> <title>` | Create a broadcast (auto-start, no archive, DVR off) bound to that stream |
| `retitle <label> <video-id> <title>` | Update a running broadcast's title (daily dated titles) |
| `cleanup <label>` | Delete the operator's own ended/stray broadcasts |

The actual video feed is produced separately (ffmpeg pushing RTMP); this tool only manages broadcast metadata.

## Setup

1. Create a Google Cloud project, enable **YouTube Data API v3**, create an **OAuth client (Desktop app)**, and save the JSON as `client_secret.json` next to `yt_api.py`.
2. Run `python3 yt_api.py auth <label>` and approve with the Google account that owns the channel.
3. Use `key` / `go-live` / `cleanup` as needed. Python 3.9+ standard library only — no dependencies.

## API usage footprint

Typical usage is a handful of daily broadcast operations: roughly **20–100 quota units per day** across 1–3 channels owned by the operator. No polling, no bulk data retrieval, no third-party traffic.

## Privacy

See [PRIVACY.md](PRIVACY.md). In short: the tool accesses only the operator's own channel data, stores OAuth tokens locally on the operator's machine, collects nothing from anyone else, and shares nothing with third parties.

## License

MIT — see [LICENSE](LICENSE).
