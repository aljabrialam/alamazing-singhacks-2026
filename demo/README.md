# Demo capture

A silent 2:30 screen recording of the deployed workbench, plus the
narration — burned in below the picture, and as a cue sheet for adding a
voice-over later.

| File | What |
|---|---|
| `out/divergence-demo-captioned.mp4` | **Play this to a room with no sound.** 1920×1300 — 1080p picture with a 220px caption band beneath it. |
| `out/divergence-demo.mp4` | The clean master. 2560×1440, no captions, no audio track. |
| `out/divergence-demo.srt` | Soft-subtitle sidecar, same lines and cues. |
| `narration.md` | Voice-over prompt — 13 lines with start cues. |
| `out/beats.json` | The real start cue of every beat, written at record time. |
| `capture.mjs` | The Playwright session. |
| `compose.mjs` | Burns the caption band; writes the `.srt`. |
| `narration.mjs` | Generates `narration.md` from `beats.json`. |

Both videos are exactly **150.000s**, 4500 frames at 30fps, H.264,
faststart, zero audio streams.

## Getting a genuinely high-resolution capture

**`recordVideo.size` larger than the viewport does not supersample — it
pads.** A 1440×810 viewport asked to record at 2880×1620 put the page in
the top-left quadrant and filled the rest with flat `rgb(128,128,128)`.
`deviceScaleFactor` does not change this; the screencast follows the CSS
viewport. Checking the reported dimensions is not enough — the resolution
looked right and three quarters of the frame was grey.

So the viewport itself has to be large. To get 2560×1440 while keeping
the framing of the 1440px layout, the page is laid out at 1440 CSS px and
zoomed to fill:

```
html { zoom: 1.7777…; width: 1440px }
```

Media queries still see 2560px, so the desktop layout branch is
unchanged. Verified by sampling the frame's right and bottom edges for
the app's ground colour rather than for padding grey.

## Why the cues cannot drift

`capture.mjs` holds each beat for a fixed wall-clock duration and writes
the actual elapsed start of each one to `beats.json`. `narration.mjs` and
`compose.mjs` both read that file, so picture, burned-in captions, `.srt`
and prompt all carry the same cues by construction.

`narration.mjs` **fails** if a line cannot be read inside its window at
153 wpm with a second to spare. Six of the first thirteen lines overran
by up to 3.3s, which is why the check exists rather than an eyeball.
`compose.mjs` likewise fails if a caption overflows the band.

## Two honest notes

- The soft navy ring is a **capture aid** injected by `capture.mjs`, not
  product chrome. It directs the eye; nothing else about the page is
  altered. The recording is a real browser session against the live
  deployment.
- Playwright records from context creation, so the page load is in the
  raw file. ffmpeg trims that lead-in, which is why beat 1 starts at
  exactly `0:00.0`.

## Regenerating

```bash
cd demo
npm i && npx playwright install chromium
DEMO_URL=https://your-deployment node capture.mjs   # -> master + beats.json
node narration.mjs                                   # -> narration.md (checks fit)
node compose.mjs                                     # -> captioned mp4 + srt
```

Needs `ffmpeg` and `ffprobe` on `PATH`. This ffmpeg has no freetype or
libass, so the captions are rendered as PNG strips in Chromium — which
also gets the project's own typefaces and brand colours instead of Arial.

## Adding a voice-over

Hand `narration.md` and the **clean** master to a voice/post tool. It
asks for one calm narrator, −16 LUFS, and the video track untouched.
