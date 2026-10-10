# Video projects: default sound workflow

Every motion video in this repo (e.g. `v2/`) gets its sound layer from
[opus-sound-layer](https://github.com/Bodila51/opus-sound-layer), following its `PROMPT.md`.
Use this as the default for every new video unless told otherwise.

## Setup

- `git clone https://github.com/Bodila51/opus-sound-layer sound-layer` at the repo root (git-ignored).
- Run its scripts with `uv run`, from inside the video's folder (paths like `audio/kit` are relative to the cwd).
  Never rewrite the scripts and never loosen a threshold to make a check pass.
- Needs network access to: `pypi.org` + `files.pythonhosted.org` (uv packages), `kenney.nl`,
  `cdn.freesound.org`, `api.openverse.org`.

## Steps (per video, e.g. `cd v2`)

1. **Cues**: export `audio/cues.json` from the picture's own timing, never by typing frames.
   In `v2/` that is `node v2/export_cues.mjs` (reads `window.soundCues()` from `scene.html`).
   Format: `uv run ../sound-layer/scripts/mix.py --schema`. Sound only on real actions, tagged
   `cut` / `move` / `land` / `appear`. One hero per ~4 s: `"hit+boom"` with `stop_before` and
   `build`, plus a riser or reverse peaking on it.
2. **Sounds**: `uv run ../sound-layer/scripts/sfx.py kit` (first run downloads the library, give it
   10 min or run it in the background). Pick every sound yourself with
   `sfx.py browse --type <type> --like "<material, weight, mood>"`, look at `audio/browse.png`,
   and put the chosen id in the cue. One sonic family per film; vary repeats.
   Nothing fits: `sfx.py search`, check with `sfx.py sheet`, then `sfx.py add FILE --type <type> --credit "<source, licence>"`.
   Never synthesize hits, clicks or whooshes; no meme sounds.
3. **Music**: a CC0 loop that fits the video's tempo/genre (e.g. from Freesound via Openverse,
   `license=cc0`), or the user's own track. Not a procedural `music.py` track. One track per video.
4. **Build**: render the picture muted (`node render.mjs video out/video_noaudio.mp4 60`), then
   `uv run ../sound-layer/scripts/mix.py audio/cues.json`, then
   `ffmpeg -i out/video_noaudio.mp4 -i audio/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest out/final.mp4`.
5. **Verify**: `uv run ../sound-layer/scripts/qa.py out/final.mp4`. Fix every FAIL by changing cues or
   sounds, at most 2 rounds. Open `audio/qa.png` and describe what it shows at each hero cue.
6. **Deliver**: `out/final.mp4`, `audio/kit/CREDITS.md` (plus the music credit), and `LISTEN.md` with
   5 timecodes to check by ear. Don't call the sound good; report what the checks show.
