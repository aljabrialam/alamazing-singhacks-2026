# Demo capture

A silent 2:30 screen recording of the deployed workbench, plus the
voice-over prompt whose cues come from that recording.

| File | What |
|---|---|
| `out/divergence-demo.mp4` | The video. Silent, 150.000s, 1440×810, 30fps, H.264, faststart. |
| `narration.md` | The voice-over prompt — 13 lines with start cues. |
| `out/beats.json` | The real start cue of every beat, written at record time. |
| `capture.mjs` | The Playwright session that produces the video. |
| `narration.mjs` | Generates `narration.md` from `beats.json`. |

## Why the cues cannot drift

`capture.mjs` holds each beat for a fixed wall-clock duration and writes
the actual elapsed start of each one to `beats.json`. `narration.mjs`
reads that file. So the cues in the prompt are the cues in the video by
construction, not by anyone keeping two documents in step.

It also **fails the build** if any line cannot be read inside its window
at 153 wpm with a second to spare. Six of the first thirteen lines
overran; that is why the check exists rather than an eyeball.

## Two honest notes

- The soft navy ring is a **capture aid** injected by `capture.mjs`, not
  product chrome. It exists to direct the eye on a 1440px frame. Nothing
  else about the page is altered — the recording is a real browser
  session against the live deployment.
- Playwright records from context creation, so the page load is in the
  raw file. ffmpeg trims that lead-in, which is why beat 1 starts at
  exactly `0:00.0` and the output is exactly 150.000s.

## Regenerating

```bash
cd demo
npm i && npx playwright install chromium
DEMO_URL=https://your-deployment node capture.mjs
node narration.mjs
```

`capture.mjs` needs `ffmpeg` and `ffprobe` on `PATH`.

## Adding the voice-over

`narration.md` is written to be handed to a voice/post tool as-is. It
asks for one calm narrator, −16 LUFS, and the video track untouched.
