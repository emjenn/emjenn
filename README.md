# 20 FREE Claude AI Courses: motion graphic

15 s · 1920×1080 (16:9) · 60 fps · H.264 + AAC. Final file: `out/claude-courses-20-free.mp4`.

Everything is generated from code:

- `src/scene.html`: canvas animation with a deterministic `renderFrame(t)` (black base, Claude palette, `x.com/nrqa__` watermark top-left / centre / bottom-right)
- `src/music.py`: procedural 120 BPM synthwave track, beat-locked to the scene cuts
- `src/render.mjs`: headless Chromium (Playwright), renders frames and pipes them into ffmpeg

Rebuild:

```bash
python3 src/music.py out/music.wav
node src/render.mjs video out/video_noaudio.mp4 60
ffmpeg -i out/video_noaudio.mp4 -i out/music.wav -af loudnorm=I=-14:TP=-1 \
  -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart out/claude-courses-20-free.mp4
```

---

# 10 free AI courses from top tech companies (`v2/`)

Exactly 15.000 s · 1920×1080 · 60 fps (900 frames). Final: `v2/out/ai-courses-10-free.mp4` (+ `_share.mp4`, smaller).

- `v2/cutout.py`: pulls the 10 reference logos out of the brand PDF and removes their white/grey/checkerboard backgrounds (colours and proportions untouched) → `v2/logos/`
- `v2/music.py`: a different track: 128 BPM tech-house in F minor (organ stabs, acid bass, a zap on every company cut)
- `v2/scene.html` + `v2/render.mjs`: same render pipeline as above
