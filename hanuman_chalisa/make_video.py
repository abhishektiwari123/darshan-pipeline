#!/usr/bin/env python3
"""Turn a song (mp3/m4a/wav/...) + the cover into a YouTube-ready MP4.

The MP4 is encoded so it works both as a normal upload and as a live-stream
source that ffmpeg can loop with `-c copy` (see stream_live.sh):
  H.264 High, 1920x1080, 30 fps, keyframe every 2 s, yuv420p
  AAC-LC 192 kbps, 48 kHz stereo, faststart

Usage:
  python3 make_video.py song.mp3                     # -> out/hanuman-chalisa.mp4
  python3 make_video.py song.mp3 --repeat 11         # 11 paath back to back
  python3 make_video.py song.mp3 --waveform          # animated gold waveform strip
  python3 make_video.py song.mp3 --cover my.png --out out/shanivar.mp4

Run make_cover.py first (or pass --cover) so out/cover.png exists.
"""

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("song", help="audio file you have the rights to use")
    p.add_argument("--cover", default=os.path.join(HERE, "out", "cover.png"))
    p.add_argument("--out", default=os.path.join(HERE, "out", "hanuman-chalisa.mp4"))
    p.add_argument("--repeat", type=int, default=1, help="play the song N times in a row")
    p.add_argument("--waveform", action="store_true", help="overlay a waveform strip at the bottom")
    a = p.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found - install it first (https://ffmpeg.org/download.html)")
    for f in (a.song, a.cover):
        if not os.path.exists(f):
            sys.exit(f"missing: {f}")
    if a.repeat < 1:
        sys.exit("--repeat must be at least 1")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)

    if a.waveform:
        graph = ("[1:a]asplit=2[aout][aw];"
                 "[aw]showwaves=s=1920x140:mode=cline:rate=30:colors=0xFFD740,"
                 "format=rgba,colorchannelmixer=aa=0.85[w];"
                 "[0:v][w]overlay=0:H-h-40:format=auto:shortest=1,format=yuv420p[v]")
        maps = ["-filter_complex", graph, "-map", "[v]", "-map", "[aout]"]
    else:
        maps = ["-vf", "scale=1920:1080,format=yuv420p", "-map", "0:v", "-map", "1:a"]

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", "-stats",
           "-loop", "1", "-framerate", "30", "-i", a.cover,
           "-stream_loop", str(a.repeat - 1), "-i", a.song,
           *maps,
           "-c:v", "libx264", "-preset", "medium", "-profile:v", "high",
           "-tune", "stillimage", "-r", "30", "-g", "60", "-keyint_min", "60",
           "-sc_threshold", "0", "-b:v", "2000k", "-maxrate", "3000k", "-bufsize", "6000k",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-shortest", "-movflags", "+faststart", a.out]
    print("running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"\nvideo ready: {a.out}")


if __name__ == "__main__":
    main()
