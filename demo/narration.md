# Prompt — narrate & stitch `divergence-demo.mp4`

You are a video post-production assistant. Add a spoken voice-over to the
attached screen recording and return the finished video. Everything you
need is below.

## Input

- `divergence-demo.mp4` — a silent screen recording, total **2:30.0** (no audio track), 1440×810, 30 fps, H.264. Inspect it to confirm.
- The numbered narration lines in **Narration** below. Each has a start cue
  in `m:ss.s` measured from the very start of the video.

The recording is a real browser session against https://web-6a5tpt22u-aljs-projects.vercel.app — not a mock-up.
The soft navy ring that appears around elements is a capture aid added by
the recording script to direct the eye; it is not part of the product.

## Task

1. Generate spoken audio for every numbered line. Voice: one calm,
   confident narrator; documentary / explainer tone, not an advert;
   unhurried. British or neutral international English.
2. Each line must **begin at its start cue**. Never start earlier. If a
   line would overrun the next cue, you may start the next line up to
   **1.0 s late** or trim leading/trailing silence — do not speed the
   speech past a natural pace.
3. Leave the video track untouched — same resolution, frame rate, length
   and pixels. Add an audio track only.
4. Silence between lines is fine and wanted. Any music bed is optional,
   must sit below −26 LUFS and duck to −30 dB under speech.
5. Master the voice to **−16 LUFS** integrated (stereo), true peak
   **≤ −1.5 dBTP**.
6. Export H.264 MP4 + AAC 192 kbps, `+faststart`. Name it
   `divergence-demo-narrated.mp4`.

## Pronunciation

- `CL-0019` → "client zero-zero-nineteen" (only if read at all)
- `BALG` → "the Balanced Growth mandate"
- `42.1%` → "forty-two point one per cent"
- `USD 32.2m` → "thirty-two point two million US dollars"
- `−2.51m` → "two point five one million"
- `7.80%` → "seven point eight per cent"
- `Al-Mansoori` → "al-man-SOO-ree"
- `Strait` → as in the Strait of Hormuz
- Dates read naturally: `2026-08-12` → "the twelfth of August"

## Do not

- Do not paraphrase, shorten, reorder or merge the lines — read each
  verbatim.
- Do not add narration to moments that have no line; let the visuals
  breathe.
- Do not alter, cover or comment on the on-screen text.
- Do not add a call to action, a product tagline, or an outro.

## Narration

13 lines. Format: `[start cue] line`.

1. **[0:00.0]** This is the first screen a relationship manager sees. Not a dashboard — a ranked list of who to call.
2. **[0:10.0]** Three conversations worth having this week. Seven clients with nothing to raise — checked, and clean. Every count is derived, never typed.
3. **[0:22.0]** Each row carries one sentence that can be defended, ordered by urgency rather than portfolio size.
4. **[0:32.0]** Abdullah Al-Mansoori. Forty-nine, Balanced Growth, thirty-two point two million. He asked a question in August that still has no answer.
5. **[0:44.0]** His objective, on file since two thousand and fourteen: build wealth outside the Gulf, and outside shipping. Forty-two per cent of the portfolio is energy and industrials.
6. **[0:56.0]** On any allocation report these are four separate things — two funds, a stock, a structured product. It looks diversified.
7. **[1:08.0]** Look through the note, and they are one bet. It references two names already held outright.
8. **[1:20.0]** Four positions. Forty-two point one per cent. One concentrated bet — read from a single record.
9. **[1:30.0]** Now the mandate. Every band, against what the portfolio actually holds.
10. **[1:40.0]** Every band is respected. Nothing in this bank's monitoring would raise anything here — and it is still forty-two per cent one bet. That gap is the product.
11. **[1:53.0]** He asked what happens if the Strait reopens. Two and a half million comes off the portfolio, and his charter rates fall the same week.
12. **[2:05.0]** The opening line, drafted from the findings above. Every figure in it was computed before the sentence was written.
13. **[2:17.0]** Every sentence traces to a row — the file, the identifiers, the values. A finding without evidence is not shown.

## Beat reference

Context only — what is on screen at each cue. Do not read this aloud.

| Start | End | On screen |
|------:|----:|-----------|
| 0:00.0 | 0:10.0 | The call list, top of page — twenty clients, ranked |
| 0:10.0 | 0:22.0 | Spotlight: the derived summary line (3 briefed / 10 watching / 7 clean) |
| 0:22.0 | 0:32.0 | Scrolling the ranked list — one defensible sentence per row |
| 0:32.0 | 0:44.0 | Client brief opens — the navy hero panel, 46px name |
| 0:44.0 | 0:56.0 | Spotlight: the quoted objective and the 42.1% headline figure |
| 0:56.0 | 1:08.0 | The four exposure blocks, separated and labelled |
| 1:08.0 | 1:20.0 | THE ORCHESTRATED MOMENT — button pressed, four blocks merge into one |
| 1:20.0 | 1:30.0 | Spotlight: the merged bar — one combined figure, 42.1% |
| 1:30.0 | 1:40.0 | The mandate panel scrolls in — the five band markers draw themselves once |
| 1:40.0 | 1:53.0 | Spotlight: the verdict block — every band respected, no breach |
| 1:53.0 | 2:05.0 | The scenario panel — the question he asked, answered |
| 2:05.0 | 2:17.0 | The opening line on the deep navy panel, 33px |
| 2:17.0 | 2:30.0 | The evidence column — file, row identifiers, values |

## Regenerating

The video and these cues are produced together, so they cannot drift:

```bash
cd demo
npm i && npx playwright install chromium
DEMO_URL=<deployment> node capture.mjs   # -> out/divergence-demo.mp4 + out/beats.json
node narration.mjs                        # -> narration.md, from those timings
```
