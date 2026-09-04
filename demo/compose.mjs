/**
 * Burn the narration into a caption band BELOW the frame.
 *
 *   node compose.mjs
 *
 * Produces:
 *   out/divergence-demo-captioned.mp4   1920x1300, narration readable, silent
 *   out/divergence-demo.srt             the same lines as a soft-subtitle sidecar
 *
 * The clean master (`out/divergence-demo.mp4`, 2560x1440) is left alone,
 * because the voice-over prompt asks for the video track untouched. The
 * captioned file is the one to play to a room with no sound.
 *
 * Why the captions are rendered in a browser rather than by ffmpeg:
 * this ffmpeg is built without freetype and libass, so `drawtext` and
 * `subtitles` do not exist — verified, not assumed. Rendering the strips
 * as PNGs in Chromium is better anyway. It gets the project's real
 * typefaces and brand colours, and proper text wrapping, instead of
 * Arial and a manual character count.
 *
 * The band sits UNDER the picture rather than over it, so it never covers
 * a figure — the whole point of the video is the numbers on screen.
 */
import { chromium } from "playwright";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const here = import.meta.dirname;
const OUT = join(here, "out");
const STRIPS = join(OUT, "captions");

const meta = JSON.parse(readFileSync(join(OUT, "beats.json"), "utf8"));
const { totalMs, cues } = meta;

const VIDEO_W = 1920;
const VIDEO_H = 1080;
const BAND_H = 220;
const TOTAL_H = VIDEO_H + BAND_H;

rmSync(STRIPS, { recursive: true, force: true });
mkdirSync(STRIPS, { recursive: true });

/* ---------------------------------------------------------------- */
/* 1. render one caption strip per cue                              */
/* ---------------------------------------------------------------- */

const strip = (n, of, text) => `<!doctype html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500&family=Archivo:wght@400;500&display=swap" rel="stylesheet">
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:${VIDEO_W}px;height:${BAND_H}px;overflow:hidden}
  body{
    background:#0C1B33;              /* the deep navy panel colour */
    color:#fff;
    font-family:'Newsreader',Georgia,serif;
    display:flex;align-items:center;
    padding:0 96px;
    position:relative;
  }
  /* their signature edge treatment, matching the dark panels in the app */
  body::before{
    content:'';position:absolute;left:0;top:0;bottom:0;width:6px;
    background:#C8102E;
  }
  .n{
    font-family:'Archivo',system-ui,sans-serif;
    font-size:26px;color:rgba(255,255,255,.42);
    font-variant-numeric:tabular-nums;
    width:118px;flex:none;letter-spacing:.02em;
  }
  .t{
    font-size:42px;line-height:1.34;max-width:1560px;
    text-wrap:pretty;
  }
</style></head>
<body>
  <div class="n">${n} / ${of}</div>
  <div class="t">${text}</div>
</body></html>`;

const esc = (s) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

console.log(`rendering ${cues.length} caption strips at ${VIDEO_W}x${BAND_H}…`);

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: VIDEO_W, height: BAND_H },
  deviceScaleFactor: 1,
});

const files = [];
for (const [i, c] of cues.entries()) {
  await page.setContent(strip(i + 1, cues.length, esc(c.say)), {
    waitUntil: "load",
  });
  await page.evaluate(() => document.fonts.ready);
  const file = join(STRIPS, `cap${String(i + 1).padStart(2, "0")}.png`);
  await page.screenshot({ path: file });
  files.push(file);

  // A strip whose text overflows the band would be silently cropped, so
  // the overflow is measured rather than eyeballed.
  const over = await page.evaluate(() => {
    const t = document.querySelector(".t");
    return t.scrollHeight - t.clientHeight;
  });
  if (over > 0) {
    console.error(
      `  !! line ${i + 1} overflows the ${BAND_H}px band by ${over}px — ` +
        `shorten it in capture.mjs or raise BAND_H`
    );
    process.exitCode = 1;
  }
}
await browser.close();
if (process.exitCode) process.exit(1);
console.log(`  all ${files.length} strips fit the band`);

/* ---------------------------------------------------------------- */
/* 2. composite: scale picture, pad a band under it, overlay strips  */
/* ---------------------------------------------------------------- */

const src = join(OUT, "divergence-demo.mp4");
const dst = join(OUT, "divergence-demo-captioned.mp4");

const args = ["-y", "-i", src];
for (const f of files) args.push("-i", f);

// picture -> 1920x1080, then a band of deep navy beneath it
let chain =
  `[0:v]scale=${VIDEO_W}:${VIDEO_H}:flags=lanczos,` +
  `pad=${VIDEO_W}:${TOTAL_H}:0:0:color=0x0C1B33[base];`;

let last = "base";
cues.forEach((c, i) => {
  const start = c.startMs / 1000;
  const end = (i + 1 < cues.length ? cues[i + 1].startMs : totalMs) / 1000;
  const tag = i === cues.length - 1 ? "vout" : `v${i}`;
  chain +=
    `[${last}][${i + 1}:v]overlay=0:${VIDEO_H}:` +
    `enable='between(t,${start.toFixed(3)},${end.toFixed(3)})'[${tag}];`;
  last = tag;
});
chain = chain.replace(/;$/, "");

args.push(
  "-filter_complex", chain,
  "-map", "[vout]",
  "-an",
  "-c:v", "libx264", "-preset", "slow", "-crf", "20",
  "-pix_fmt", "yuv420p", "-r", "30",
  "-movflags", "+faststart",
  dst
);

console.log(`compositing ${VIDEO_W}x${TOTAL_H} (picture ${VIDEO_H} + band ${BAND_H})…`);
execFileSync("ffmpeg", args, { stdio: ["ignore", "ignore", "pipe"] });

/* ---------------------------------------------------------------- */
/* 3. an .srt sidecar, for players that prefer soft subtitles        */
/* ---------------------------------------------------------------- */

const srtTime = (ms) => {
  const h = Math.floor(ms / 3_600_000);
  const m = Math.floor((ms % 3_600_000) / 60_000);
  const s = Math.floor((ms % 60_000) / 1000);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(
    s
  ).padStart(2, "0")},${String(ms % 1000).padStart(3, "0")}`;
};

writeFileSync(
  join(OUT, "divergence-demo.srt"),
  cues
    .map((c, i) => {
      const end = i + 1 < cues.length ? cues[i + 1].startMs : totalMs;
      return `${i + 1}\n${srtTime(c.startMs)} --> ${srtTime(end)}\n${c.say}\n`;
    })
    .join("\n")
);

/* ---------------------------------------------------------------- */

const probe = (f) =>
  JSON.parse(
    execFileSync("ffprobe", [
      "-v", "error",
      "-show_entries", "format=duration,size",
      "-show_entries", "stream=width,height,codec_name,nb_frames",
      "-of", "json", f,
    ]).toString()
  );

for (const f of [src, dst]) {
  const p = probe(f);
  const v = p.streams.find((s) => s.codec_name);
  console.log(
    `\n${f.split("/").pop()}\n  ${v.width}x${v.height}  ${Number(
      p.format.duration
    ).toFixed(3)}s  ${(p.format.size / 1e6).toFixed(1)} MB  ${v.nb_frames} frames`
  );
}
console.log(`\n${join(OUT, "divergence-demo.srt").split("/").pop()} written`);
