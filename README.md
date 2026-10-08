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
