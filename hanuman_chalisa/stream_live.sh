#!/usr/bin/env bash
# Loop the Hanuman Chalisa MP4 to a YouTube live stream, forever (Ctrl+C to stop).
#
#   YT_KEY_HANUMAN=xxxx-xxxx-xxxx-xxxx ./stream_live.sh out/hanuman-chalisa.mp4
#
# Get the key with:  python3 ../yt_api.py key spiritual hanuman
# The MP4 from make_video.py is already live-friendly (2 s keyframes), so it is
# sent with -c copy: almost no CPU used. If ffmpeg drops the connection it is
# restarted after 5 s.
set -euo pipefail

VIDEO="${1:-$(dirname "$0")/out/hanuman-chalisa.mp4}"
KEY="${YT_KEY_HANUMAN:?set YT_KEY_HANUMAN to your stream key}"
URL="rtmp://a.rtmp.youtube.com/live2/${KEY}"

[ -f "$VIDEO" ] || { echo "missing video: $VIDEO" >&2; exit 1; }

while true; do
  ffmpeg -hide_banner -loglevel warning -stats \
    -re -stream_loop -1 -fflags +genpts -i "$VIDEO" \
    -c copy -f flv "$URL" || true
  echo "stream dropped - reconnecting in 5 s" >&2
  sleep 5
done
