/**
 * Generate the voice-over prompt from the REAL capture timings.
 *
 * Reads `out/beats.json`, written by capture.mjs at record time, and
 * writes `narration.md`. The cues are therefore the cues in the file
 * rather than an estimate of them — if a beat drifts, this drifts with
 * it, and the two can never disagree.
 *
 *   node compose.mjs && node narration.mjs
 *
 * The prompt targets the CAPTIONED cut, because that is the one being
 * shown. Its narration is already burned into the band under the
 * picture, in sync with these same cues — so a spoken line that departs
 * from its text would visibly contradict what the audience is reading.
 * That turns "read verbatim" from a style note into a hard requirement,
 * and the prompt says so.
 *
 * Resolution, duration and frame rate are probed from the file rather
 * than copied from beats.json, so the prompt cannot describe a video
 * that is not the one attached.
 */
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const here = import.meta.dirname;
const { site, totalMs, cues } = JSON.parse(
  readFileSync(join(here, "out", "beats.json"), "utf8")
);

const TARGET = "divergence-demo-captioned.mp4";
const targetPath = join(here, "out", TARGET);
if (!existsSync(targetPath)) {
  console.error(`${TARGET} not found — run \`node compose.mjs\` first.`);
  process.exit(1);
}

const probe = JSON.parse(
  execFileSync("ffprobe", [
    "-v", "error",
    "-show_entries", "format=duration",
    "-show_entries", "stream=width,height,codec_name,r_frame_rate,nb_frames",
    "-of", "json", targetPath,
  ]).toString()
);
const vs = probe.streams.find((s) => s.width);
const width = vs.width;
const height = vs.height;
const fps = Math.round(eval(vs.r_frame_rate));
const frames = vs.nb_frames;
const fileDurMs = Math.round(Number(probe.format.duration) * 1000);

// The burned-in captions and these cues come from the same beats.json,
// so a length mismatch would mean the two have drifted apart.
if (Math.abs(fileDurMs - totalMs) > 100) {
  console.error(
    `${TARGET} is ${(fileDurMs / 1000).toFixed(3)}s but beats.json says ` +
      `${(totalMs / 1000).toFixed(3)}s — recompose before generating the prompt.`
  );
  process.exit(1);
}

const audioStreams = execFileSync("ffprobe", [
  "-v", "error", "-select_streams", "a",
  "-show_entries", "stream=index", "-of", "csv=p=0", targetPath,
]).toString().trim();

const cue = (ms) => {
  const s = ms / 1000;
  return `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, "0")}`;
};

/**
 * A cue sheet whose lines cannot be read in the gap before the next cue
 * is not a cue sheet — the narrator either rushes or the audio drifts out
 * of sync with the picture.
 *
 * Six of the first thirteen lines overran, so this is checked rather than
 * eyeballed. 2.55 words/second is roughly 153 wpm: an unhurried
 * documentary read, which is what the prompt asks for.
 */
const WORDS_PER_SEC = 2.55;
const MIN_SLACK_SEC = 1.0;

function checkFit() {
  const rows = cues.map((c, i) => {
    const next = i + 1 < cues.length ? cues[i + 1].startMs : totalMs;
    const windowSec = (next - c.startMs) / 1000;
    const words = (c.say.match(/[\w’'-]+/g) ?? []).length;
    const needSec = words / WORDS_PER_SEC;
    return { n: i + 1, id: c.id, windowSec, words, needSec, slack: windowSec - needSec };
  });

  console.log(`  #  cue      win  words  needs  slack`);
  for (const r of rows) {
    const flag = r.slack < MIN_SLACK_SEC ? "  <-- TOO TIGHT" : "";
    console.log(
      `  ${String(r.n).padStart(2)}  ${String(r.windowSec.toFixed(0)).padStart(3)}s` +
        `     ${String(r.words).padStart(3)}  ${r.needSec.toFixed(1).padStart(5)}s` +
        `  ${(r.slack >= 0 ? "+" : "") + r.slack.toFixed(1)}s${flag}`
    );
  }

  const bad = rows.filter((r) => r.slack < MIN_SLACK_SEC);
  if (bad.length) {
    console.error(
      `\n${bad.length} line(s) cannot be read at ${(WORDS_PER_SEC * 60).toFixed(
        0
      )} wpm with ${MIN_SLACK_SEC}s to spare:`
    );
    for (const r of bad) {
      console.error(`  line ${r.n} (${r.id}): ${r.slack.toFixed(1)}s slack`);
    }
    console.error("\nShorten the line or lengthen the beat in capture.mjs.");
    process.exit(1);
  }
  console.log(`\n  all ${rows.length} lines fit with >= ${MIN_SLACK_SEC}s to spare`);
}

checkFit();

const lines = cues
  .map((c, i) => `${i + 1}. **[${cue(c.startMs)}]** ${c.say}`)
  .join("\n");

const table = cues
  .map(
    (c, i) =>
      `| ${cue(c.startMs)} | ${cue(
        i + 1 < cues.length ? cues[i + 1].startMs : totalMs
      )} | ${c.on} |`
  )
  .join("\n");

const doc = `# Prompt — narrate & stitch \`${TARGET}\`

You are a video post-production assistant. Add a spoken voice-over to the
attached screen recording and return the finished video. Everything you
need is below.

## Input

- \`${TARGET}\` — a silent screen recording, total **${cue(
  totalMs
)}** (${audioStreams ? "HAS an audio track — remove it" : "no audio track"}), ${width}×${height}, ${fps} fps, H.264, ${frames} frames. Inspect it to confirm.
- The numbered narration lines in **Narration** below. Each has a start cue
  in \`m:ss.s\` measured from the very start of the video.

## The narration is already on screen — this matters

The bottom **${height - 1080}px** of the frame is a caption band, dark navy
with a red rule at its left edge. It already displays the narration line
for the current beat, in sync with the cues below, numbered \`n / ${
  cues.length
}\`.

**So each spoken line must match the on-screen text word for word.** A
paraphrase, a dropped clause or a reordered sentence will visibly
contradict what the audience is reading at that moment. This is the
strictest requirement in the prompt.

The band is part of the picture. Do not crop it, cover it, redraw it,
replace it with your own subtitles, or add a second caption layer.

The recording above the band is a real browser session against ${site} —
not a mock-up. The soft navy ring around elements is a capture aid added
by the recording script to direct the eye; it is not part of the product.

## Task

1. Generate spoken audio for every numbered line. Voice: one calm,
   confident narrator; documentary / explainer tone, not an advert;
   unhurried. British or neutral international English.
2. Each line must **begin at its start cue**. Never start earlier. If a
   line would overrun the next cue, you may start the next line up to
   **1.0 s late** or trim leading/trailing silence — do not speed the
   speech past a natural pace.
3. Leave the video track untouched — same resolution, frame rate, length
   and pixels, **including the caption band**. Add an audio track only.
4. Silence between lines is fine and wanted. Any music bed is optional,
   must sit below −26 LUFS and duck to −30 dB under speech.
5. Master the voice to **−16 LUFS** integrated (stereo), true peak
   **≤ −1.5 dBTP**.
6. Export H.264 MP4 + AAC 192 kbps, \`+faststart\`. Name it
   \`divergence-demo-captioned-narrated.mp4\`.

## Pronunciation

- \`Al-Mansoori\` → "al-man-SOO-ree"; \`Abdullah\` → "ab-DOO-lah"
- \`Strait\` → as in the Strait of Hormuz
- "two thousand and fourteen" read as written, not "twenty fourteen"
- **Codes on screen are never spoken.** \`CL-0019\`, \`SYN-EQ-0008\`,
  \`BALG\` and \`N-026\` appear in the picture but in none of the lines.
- Every figure is already spelled out in the lines. Read it as written;
  do not convert back to digits, and do not round.

## Do not

- Do not paraphrase, shorten, reorder or merge the lines — read each
  **verbatim**. The same words are on screen; any change is visible.
- Do not add narration to moments that have no line; let the visuals
  breathe.
- Do not alter, cover or comment on the on-screen text.
- Do not crop or letterbox to a 16:9 frame — that would cut the caption
  band off the bottom.
- Do not burn in your own subtitles. The video already has them.
- Do not add a call to action, a product tagline, or an outro.

## Narration

${cues.length} lines. Format: \`[start cue] line\`.

${lines}

## Beat reference

Context only — what is on screen at each cue. Do not read this aloud.

| Start | End | On screen |
|------:|----:|-----------|
${table}

## Regenerating

The video and these cues are produced together, so they cannot drift:

\`\`\`bash
cd demo
npm i && npx playwright install chromium
DEMO_URL=<deployment> node capture.mjs   # -> out/divergence-demo.mp4 + out/beats.json
node narration.mjs                        # -> narration.md, from those timings
\`\`\`
`;

writeFileSync(join(here, "narration.md"), doc);
console.log(`narration.md written — ${cues.length} lines, ${cue(totalMs)} total`);
for (const [i, c] of cues.entries()) {
  console.log(`  ${String(i + 1).padStart(2)}. [${cue(c.startMs)}] ${c.id}`);
}
