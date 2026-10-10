# Motion videos in this repo

Every motion video here follows the same defaults unless the user says otherwise.

## Picture
- 16:9, 1920x1080, black base.
- Watermark `x.com/nrqa__` on every frame: top-left, centre and bottom-right.
- Deterministic `renderFrame(t)` in an HTML scene, rendered frame by frame with
  Playwright + ffmpeg (see `v2/scene.html` and `v2/render.mjs`).
- The scene exposes `window.soundCues()` built from its own timing constants, and
  `export_cues.mjs` writes `audio/cues.json` from it. Never type cue times by hand.

## Sound: the opus-sound-layer workflow (default for every video)
Real recordings only, placed from the picture's timeline, checked by measurement.

SETUP: `git clone https://github.com/Bodila51/opus-sound-layer sound-layer` at the
repo root (git-ignored). Use its scripts with `uv run` (needs ffmpeg + uv). Never
rewrite them, never loosen a threshold to make a check pass. Run from the
project folder (e.g. `v2/`) so `audio/` resolves there.

1. CUES: export `audio/cues.json` from the scene's own timing
   (`uv run ../sound-layer/scripts/mix.py --schema` for the format). Sound only on
   real actions, tagged cut / move / land / appear. One hero per ~4 s:
   `"hit+boom"` with `stop_before` and `build`, plus a riser or reverse peaking on it.
2. SOUNDS: `uv run ../sound-layer/scripts/sfx.py kit` (first run downloads the
   library, allow ~10 min). Pick every sound yourself with
   `sfx.py browse --type <type> --like "<material, weight, mood>"`, look at
   `audio/browse.png`, put the chosen id in the cue. One sonic family per film;
   vary repeats. If nothing fits: `sfx.py search`, check with `sfx.py sheet`, then
   `sfx.py add FILE --type <type> --credit "<source, licence>"`.
   Never synthesize hits, clicks or whooshes. No meme sounds.
   MUSIC: CC0 (e.g. Openverse / Freesound) or a track the user supplies. Never
   composed by Claude. Use a different track for every project. Record title,
   creator, licence and URL in `audio/MUSIC_CREDIT.md`. Line a strong downbeat up
   with the main drop (`music.start_s`).
3. BUILD:
   ```
   uv run ../sound-layer/scripts/mix.py audio/cues.json
   ffmpeg -i video.mp4 -i audio/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest out/final.mp4
   uv run ../sound-layer/scripts/qa.py out/final.mp4
   ```
4. VERIFY: `qa.py` must pass. Fix FAILs by changing cues or sounds (max 2 rounds),
   then look at `audio/qa.png` at each hero cue.
5. DELIVER: `out/final.mp4`, a share copy under 30 MB
   (`-c:v libx264 -crf 21 -c:a copy` → `out/final_share.mp4`), `audio/CREDITS.md`
   (copied from `audio/kit/CREDITS.md`), `LISTEN.md` with 5 timecodes to check by
   ear. Report what the checks show (paste the qa.py table); don't call the sound good.

Don't commit `sound-layer/`, `audio/kit/`, `audio/stems/` or the muted `video.mp4`.
