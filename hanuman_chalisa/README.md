# Hanuman Chalisa – शनिवार स्पेशल template

Everything needed to turn **your own Hanuman Chalisa audio** into a Saturday-special
YouTube video / 24×7 live stream on your spiritual channel.

| File | What it is |
|---|---|
| `make_cover.py` | Draws the 1920×1080 cover (video background) + 1280×720 thumbnail |
| `make_video.py` | Song + cover → upload-ready **MP4** (H.264 + AAC, 1080p30) |
| `stream_live.sh` | Loops that MP4 to your YouTube live stream key, forever |
| `glabs_art.py` | Makes Hanuman ji artwork with G-Labs Studio (Meta Muse / Meta AI) and puts it in the cover |
| `metadata.json` | Trending title, description and tags (Hindi + English) |
| `out/cover.png`, `out/cover-thumb.jpg` | Ready-made cover and thumbnail |
| `fonts/` | Noto Devanagari + Noto Sans (SIL OFL, see `fonts/OFL.txt`) |

Requirements: Python 3.9+, `pip install pillow`, and `ffmpeg`.

## 1. Cover and thumbnail

```bash
python3 make_cover.py                                  # default शनिवार स्पेशल design
python3 make_cover.py --image hanuman.png              # your Hanuman ji picture in the circle
python3 make_cover.py --day "मंगलवार स्पेशल"             # Tuesday version
python3 make_cover.py --tagline "11 बार पाठ"             # line next to LIVE
python3 make_cover.py --no-live                        # normal (non-live) upload
```

### Hanuman ji artwork with G-Labs Studio (Meta Muse / Meta AI)

Run this on the PC where G-Labs Studio is open (**Webhook** tab → **Start**, MAX plan,
a Muse or Meta AI account logged in):

```bash
set GLABS_API_KEY=key-from-webhook-tab          # Windows (export ... on Linux/macOS)
python3 glabs_art.py                            # Meta Muse, 2 images, 1st goes in the cover
python3 glabs_art.py --engine meta              # Meta AI instead
python3 glabs_art.py --count 4 --pick 3         # make 4, use the 3rd
```

Images are saved to `out/glabs/` and `out/cover.png` / `out/cover-thumb.jpg` are rebuilt
with the chosen one. Then run `make_video.py` again so the MP4 uses the new cover.

## 2. Make the MP4

```bash
python3 make_video.py my-hanuman-chalisa.mp3                 # out/hanuman-chalisa.mp4
python3 make_video.py my-hanuman-chalisa.mp3 --repeat 11     # 11 paath in one video
python3 make_video.py my-hanuman-chalisa.mp3 --waveform      # moving gold waveform
```

Output: MP4, H.264 High 1920×1080 30 fps, keyframe every 2 s, AAC 192 kbps 48 kHz.
This is YouTube's recommended format for uploads **and** is safe to stream with
`-c copy`.

## 3. Go live (loops the MP4 24×7)

```bash
python3 ../yt_api.py auth spiritual                    # once, with the channel's Google account
python3 ../yt_api.py key spiritual hanuman             # prints YT_KEY_HANUMAN=...
python3 ../yt_api.py go-live spiritual hanuman "🔴 LIVE शनिवार स्पेशल हनुमान चालीसा"
#   -> prints watch: https://youtube.com/watch?v=VIDEO_ID
python3 ../yt_api.py meta spiritual VIDEO_ID metadata.json "Singer / label name"
python3 ../yt_api.py thumbnail spiritual VIDEO_ID out/cover-thumb.jpg

YT_KEY_HANUMAN=xxxx-xxxx-xxxx-xxxx ./stream_live.sh out/hanuman-chalisa.mp4
```

Without the API you can do the same by hand: YouTube Studio → **Create → Go live →
Stream**, copy the stream key, run `stream_live.sh`, then paste the title, description
and tags from `metadata.json` and upload `out/cover-thumb.jpg` as the thumbnail.
(Or use OBS: add `out/hanuman-chalisa.mp4` as a *Media Source* with **Loop** ticked.)

`{date}` in the title/description is filled with today's date by `yt_api.py meta`;
`{audio_credit}` with the credit you pass. Next Saturday, run `meta` again (or
`retitle`) to refresh the date without stopping the stream.

## Copyright – read before going live

The Chalisa **text** is public domain, but every **recording** (T-Series / Gulshan
Kumar, Hariharan, etc.) is owned by someone. Using one you don't have rights to gets the
live stream muted or taken down by Content ID and can earn your channel a strike. Use
your own recording, a royalty-free track whose licence allows streaming, or one you
have permission for, and put that credit in `{audio_credit}`.
