# Music credit

- **Title:** Melody Loop Mix 128 bpm
- **Creator:** DaveJf
- **Licence:** CC0 1.0 (public domain), https://creativecommons.org/publicdomain/zero/1.0/
- **Source:** https://freesound.org/people/DaveJf/sounds/578141 (found through the Openverse API, file: https://cdn.freesound.org/previews/578/578141_11861866-hq.mp3)

## How it's used
- 128 BPM, same as the picture's grid. The file opens with an 8-bar quiet section, then the full
  beat comes in at ~15.06 s.
- `audio/music.wav` is cut from 13.185 s in the original (`ffmpeg -ss 13.185 -t 15.2`), so the
  loop's own drop lands on the picture's 1.875 s drop. The film's 15 s then plays inside the
  loop's full section (no looping needed).
- This replaces the old procedurally generated F-minor tech-house track (`out/music.wav`, `music.py`).
