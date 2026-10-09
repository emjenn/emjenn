# emjenn — motion graphics videos for x.com/nrqa__

Each project lives in `video/<project>/` with `motion.html` (canvas animation, `render(t, frame)`),
`music.py` (fully synthesized soundtrack → `build/music.wav`) and `render.js` (Playwright → ffmpeg).
Render: `python3 music.py build/music.wav && NODE_PATH=$(npm root -g) node render.js video out.mp4 60`.

## Rules for every video
- **Every video gets its own, different music.** Never reuse a previous project's track or just
  re-key it — change genre/groove/sound palette. Tracks so far:
  - `video/music.py` (Claude courses): synthwave/house, 128 BPM, A minor
  - `video/ai-courses/music.py`: electro / future-house, 128 BPM, D minor, 808 + growl bass
  - `video/fullenrich/music.py`: dark phonk / half-time trap, 128 BPM, C# Phrygian, cowbell lead, tape stop
  Keep `KICKS` in `motion.html` in sync with the new track's drum pattern.
- Black background base; text and animation in the featured companies' brand colours.
- 16:9, 1920×1080, 60fps, 15s.
- Watermark `x.com/nrqa__`: small and semi-transparent, top-left, bottom-right and centre.
- Also export a `*-preview.mp4` (crf 22) under 30 MB for sharing.
