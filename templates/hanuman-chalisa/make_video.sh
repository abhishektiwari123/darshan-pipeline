#!/usr/bin/env bash
# Hanuman Chalisa song + cover -> YouTube-ready MP4 (also safe to loop for live).
#
# Usage:
#   ./make_video.sh <song.mp3|wav|m4a> [cover.png] [repeat] [out.mp4]
#
#   song    your Hanuman Chalisa audio
#   cover   default: out/cover.png (run make_cover.py first)
#   repeat  how many times to play the song back-to-back (default 1;
#           e.g. 11 for "11 baar Hanuman Chalisa")
#   out     default: out/hanuman-chalisa-shanivar-special.mp4
#
# Output: MP4, H.264 High 1920x1080 30fps yuv420p, keyframe every 2 s,
# AAC 192 kbps 48 kHz stereo, +faststart. These are YouTube's recommended
# upload / live-ingest settings, so the same file can be uploaded as a video
# or pushed with `-c copy` to the live RTMP endpoint (see README.md).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SONG="${1:?usage: make_video.sh <song> [cover.png] [repeat] [out.mp4]}"
COVER="${2:-$HERE/out/cover.png}"
REPEAT="${3:-1}"
OUT="${4:-$HERE/out/hanuman-chalisa-shanivar-special.mp4}"

[ -f "$SONG" ] || { echo "song not found: $SONG" >&2; exit 1; }
[ -f "$COVER" ] || { echo "cover not found: $COVER (run: python3 make_cover.py)" >&2; exit 1; }
mkdir -p "$(dirname "$OUT")"

# cover as the still background, a soft golden waveform along the bottom
ffmpeg -hide_banner -y \
  -loop 1 -framerate 30 -i "$COVER" \
  -stream_loop $((REPEAT - 1)) -i "$SONG" \
  -filter_complex "\
[1:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[aout][aw];\
[aw]showwaves=s=1920x120:mode=cline:rate=30:colors=0xFFD140@0.85,format=rgba[wave];\
[0:v]scale=1920:1080,format=yuv420p[bg];\
[bg][wave]overlay=0:H-150:shortest=1:format=auto,format=yuv420p[v]" \
  -map "[v]" -map "[aout]" \
  -c:v libx264 -preset medium -profile:v high -tune stillimage -crf 20 \
  -maxrate 6M -bufsize 12M -g 60 -keyint_min 60 -sc_threshold 0 -r 30 \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -shortest -movflags +faststart \
  "$OUT"

echo "done: $OUT"
