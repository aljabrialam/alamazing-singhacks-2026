/**
 * Demo capture — a silent screen recording of the deployed workbench.
 *
 * Produces:
 *   demo/out/divergence-demo.mp4   silent, exactly 150.0s (2:30), H.264
 *   demo/out/beats.json            the REAL start cue of every beat
 *
 * The narration cue sheet is generated from `beats.json` rather than
 * estimated, so the cues in the voice-over prompt are the cues in the
 * file. See `demo/narration.md`.
 *
 * Two things worth knowing about the timing:
 *
 *   1. Playwright starts recording when the browser context is created,
 *      so the page load is in the video. The script marks the moment the
 *      first beat begins and ffmpeg trims everything before it, so beat 1
 *      starts at exactly 0:00.0.
 *
 *   2. Every beat holds for a fixed wall-clock duration. Whatever the
 *      action inside it costs (a smooth scroll, a click, a network hop)
 *      is subtracted from the hold, so the beat boundaries do not drift
 *      when the network is slow.
 *
 * The spotlight ring is a capture aid and is NOT part of the product. It
 * is injected by this script and exists only to tell a viewer where to
 * look on a 1440px frame. Nothing else about the page is altered.
 */
import { chromium } from "playwright";
import { execFileSync } from "node:child_process";
import { mkdirSync, readdirSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const SITE = process.env.DEMO_URL ?? "https://web-bdqvc2a3d-aljs-projects.vercel.app";
const HERO = "CL-0019";
const OUT = join(import.meta.dirname, "out");
const RAW = join(OUT, "raw");
// True 2560x1440 capture, with the framing of a 1440px layout.
//
// `recordVideo.size` larger than the viewport does NOT supersample — it
// pads the surplus with flat grey. Measured: a 1440x810 viewport asked
// to record at 2880x1620 put the page in the top-left quadrant and
// filled the rest with rgb(128,128,128). deviceScaleFactor does not
// change this; the screencast follows the CSS viewport.
//
// So the viewport itself has to be large. To keep the framing identical
// to the 1440px layout that was already verified, the page is laid out
// at 1440 CSS px and zoomed to fill the wider viewport. Media queries
// still see 2560px, so the desktop layout branch is unchanged.
const VIEW_W = 2560;     // viewport == video size, so nothing is padded
const VIEW_H = 1440;
const LAYOUT_W = 1440;   // the width the page lays itself out at
const ZOOM = VIEW_W / LAYOUT_W;   // 1.777…

rmSync(OUT, { recursive: true, force: true });
mkdirSync(RAW, { recursive: true });

/* ------------------------------------------------------------------ */
/* The beats. `say` is the narration line; `on` is what is on screen.  */
/* `ms` is the exact hold. The sum is the video length.                */
/* ------------------------------------------------------------------ */

const beats = [
  {
    id: "call-list",
    ms: 10_000,
    on: "The call list, top of page — twenty clients, ranked",
    say:
      "This is the first screen a relationship manager sees. Not a dashboard — " +
      "a ranked list of who to call.",
    async run(p) {
      await p.evaluate(() => window.scrollTo({ top: 0 }));
    },
  },
  {
    id: "counts",
    ms: 12_000,
    on: "Spotlight: the derived summary line (3 briefed / 10 watching / 7 clean)",
    say:
      "Three conversations worth having this week. Seven clients with nothing to " +
      "raise — checked, and clean. Every count is derived, never typed.",
    async run(p) {
      await spotlight(p, "main-summary");
    },
  },
  {
    id: "rows",
    ms: 10_000,
    on: "Scrolling the ranked list — one defensible sentence per row",
    say:
      "Each row carries one sentence that can be defended, ordered by urgency " +
      "rather than portfolio size.",
    async run(p) {
      await clear(p);
      // Anchored on a row rather than a pixel offset: with the page
      // zoomed, a literal scrollTop no longer means the same distance.
      await smoothToSel(p, "ol li:nth-child(4)");
    },
  },
  {
    id: "hero",
    ms: 12_000,
    on: "Client brief opens — the navy hero panel, 46px name",
    say:
      "Abdullah Al-Mansoori. Forty-nine, Balanced Growth, thirty-two point two " +
      "million. He asked a question in August that still has no answer.",
    async run(p) {
      await p.click(`a[href="/client/${HERO}"]`);
      await p.waitForSelector(".hero-name");
      await settle(p);
      await spotlight(p, "hero");
    },
  },
  {
    id: "objective",
    ms: 12_000,
    on: "Spotlight: the quoted objective and the 42.1% headline figure",
    say:
      "His objective, on file since two thousand and fourteen: build wealth " +
      "outside the Gulf, and outside shipping. Forty-two per cent of the " +
      "portfolio is energy and industrials.",
    async run(p) {
      await spotlight(p, "hero-figure");
    },
  },
  {
    id: "four-blocks",
    ms: 12_000,
    on: "The four exposure blocks, separated and labelled",
    say:
      "On any allocation report these are four separate things — two funds, a " +
      "stock, a structured product. It looks diversified.",
    async run(p) {
      await clear(p);
      await smoothToSel(p, "#demo-exposure");
      await spotlight(p, "exposure");
    },
  },
  {
    id: "merge",
    ms: 12_000,
    on: "THE ORCHESTRATED MOMENT — button pressed, four blocks merge into one",
    say:
      "Look through the note, and they are one bet. It references two names " +
      "already held outright.",
    async run(p) {
      await clear(p);
      await p.click("button:has-text('Look through the note')");
    },
  },
  {
    id: "merged",
    ms: 10_000,
    on: "Spotlight: the merged bar — one combined figure, 42.1%",
    say:
      "Four positions. Forty-two point one per cent. One concentrated bet — " +
      "read from a single record.",
    async run(p) {
      await spotlight(p, "exposure");
    },
  },
  {
    id: "mandate",
    ms: 10_000,
    on: "The mandate panel scrolls in — the five band markers draw themselves once",
    say:
      "Now the mandate. Every band, against what the portfolio actually holds.",
    async run(p) {
      await clear(p);
      await smoothToSel(p, "#demo-mandate");
      await spotlight(p, "mandate-bands");
    },
  },
  {
    id: "verdict",
    ms: 13_000,
    on: "Spotlight: the verdict block — every band respected, no breach",
    say:
      "Every band is respected. Nothing in this bank's monitoring would raise " +
      "anything here — and it is still forty-two per cent one bet. That gap is " +
      "the product.",
    async run(p) {
      await clear(p);
      await smoothToSel(p, "[data-demo='mandate-verdict']");
      await spotlight(p, "mandate-verdict");
    },
  },
  {
    id: "scenario",
    ms: 12_000,
    on: "The scenario panel — the question he asked, answered",
    say:
      "He asked what happens if the Strait reopens. Two and a half million comes " +
      "off the portfolio, and his charter rates fall the same week.",
    async run(p) {
      await clear(p);
      await smoothToSel(p, "#demo-scenario");
      await spotlight(p, "scenario");
    },
  },
  {
    id: "opening-line",
    ms: 12_000,
    on: "The opening line on the deep navy panel, 33px",
    say:
      "The opening line, drafted from the findings above. Every figure in it was " +
      "computed before the sentence was written.",
    async run(p) {
      await clear(p);
      await smoothToSel(p, "#demo-opening");
      await spotlight(p, "opening");
    },
  },
  {
    id: "evidence",
    ms: 13_000,
    on: "The evidence column — file, row identifiers, values",
    say:
      "Every sentence traces to a row — the file, the identifiers, the values. " +
      "A finding without evidence is not shown.",
    async run(p) {
      // The evidence column is `sticky`, so scrolling "to" it moves
      // nothing — it is already on screen, which is the point (it is
      // visible without interaction by design). So close by travelling
      // back to the top instead: the hero and the head of the evidence
      // column in one frame, which reads as "all of this traces back".
      await clear(p);
      await p.evaluate(() => window.scrollTo({ top: 0, behavior: "smooth" }));
      await sleep(2400);
      await spotlight(p, "evidence");
    },
  },
];

/* ------------------------------------------------------------------ */
/* helpers                                                             */
/* ------------------------------------------------------------------ */

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function settle(p) {
  await p.evaluate(() => document.fonts.ready);
  await sleep(350);
}

async function smoothTo(p, top) {
  await p.evaluate((y) => window.scrollTo({ top: y, behavior: "smooth" }), top);
  await sleep(1100);
}

async function smoothToSelTop(p, sel, wait = 2000) {
  await p.evaluate((s) => {
    const el = document.querySelector(s);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }, sel);
  await sleep(wait);
}

async function smoothToSel(p, sel) {
  await p.evaluate((s) => {
    const el = document.querySelector(s);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
  }, sel);
  await sleep(1200);
}

/** The capture aid. A soft ring, no movement, no dimming. */
async function spotlight(p, key) {
  await p.evaluate((k) => {
    document
      .querySelectorAll("[data-demo-lit]")
      .forEach((n) => n.removeAttribute("data-demo-lit"));
    const el = document.querySelector(`[data-demo="${k}"]`);
    if (el) el.setAttribute("data-demo-lit", "1");
  }, key);
}

async function clear(p) {
  await p.evaluate(() =>
    document
      .querySelectorAll("[data-demo-lit]")
      .forEach((n) => n.removeAttribute("data-demo-lit"))
  );
}

/**
 * Tag the elements the beats point at, and install the ring.
 *
 * Tagging is done here rather than in the product so the app carries no
 * demo-only attributes. Anchors are text- and class-based, matching what
 * the live page actually renders.
 */
async function prepare(p) {
  await p.addStyleTag({
    content: `
      [data-demo-lit]{
        outline:2px solid rgba(20,40,75,.5);
        outline-offset:8px;
        border-radius:3px;
        transition:outline-color .4s ease;
      }
      [data-demo-lit].on-dark{ outline-color:rgba(201,168,118,.75); }
      /* the caret never blinks into a frame */
      *{caret-color:transparent!important}
    `,
  });
  await p.evaluate(() => {
    const tag = (el, name, dark) => {
      if (!el) return;
      el.setAttribute("data-demo", name);
      if (dark) el.classList.add("on-dark");
    };
    // textContent includes descendants, so a generic selector like
    // "div" matches every ancestor too — and the FIRST match is the
    // outermost wrapper. Take the deepest match instead: the one with
    // no descendant that also matches.
    const byText = (sel, text) => {
      const hits = [...document.querySelectorAll(sel)].filter((n) =>
        n.textContent?.includes(text)
      );
      return hits.find((n) => !hits.some((o) => o !== n && n.contains(o)));
    };

    // call list
    tag(byText("p", "clients on the desk"), "main-summary");

    // hero panel and its figure
    const heroName = document.querySelector(".hero-name");
    if (heroName) {
      tag(heroName.closest(".jb-rule"), "hero", true);
      const fig = document.querySelector(".hero-figure");
      tag(fig?.parentElement, "hero-figure", true);
    }

    // the exposure figure: the block grid's container
    const btn = [...document.querySelectorAll("button")].find((b) =>
      b.textContent?.includes("Look through the note")
    );
    const exposure = btn?.closest("div")?.parentElement;
    if (exposure) {
      exposure.id = "demo-exposure";
      tag(exposure, "exposure");
    }

    // mandate panel + verdict
    const mandateIntro = byText("div", "mandate, against what the portfolio");
    // The band rows are what must be centred — the panel as a whole is
    // taller than the viewport, so centring it frames neither end.
    const bandRows = mandateIntro?.parentElement?.querySelector(
      "[data-reveal]"
    );
    if (bandRows) {
      bandRows.id = "demo-mandate";
      tag(bandRows, "mandate-bands");
    }
    const verdict = byText("b", "Every band is respected")?.closest("div");
    if (verdict) tag(verdict, "mandate-verdict");

    // scenario
    const scenarioH = [...document.querySelectorAll("h3")].find((h) =>
      h.textContent?.includes("Brent crude returns")
    );
    const scenario = scenarioH?.parentElement;
    if (scenario) {
      scenario.id = "demo-scenario";
      tag(scenario, "scenario");
    }

    // the opening line panel
    const opening = document.querySelector(".opening-line")?.closest(".jb-rule");
    if (opening) {
      opening.id = "demo-opening";
      tag(opening, "opening", true);
    }

    // the evidence column
    const evidence = [...document.querySelectorAll("h2,h3")]
      .find((h) => h.textContent?.trim() === "Evidence")
      ?.parentElement;
    if (evidence) {
      evidence.id = "demo-evidence";
      tag(evidence, "evidence");
    }
  });
}

/* ------------------------------------------------------------------ */
/* run                                                                 */
/* ------------------------------------------------------------------ */

const total = beats.reduce((n, b) => n + b.ms, 0);
console.log(`site   ${SITE}`);
console.log(`beats  ${beats.length}`);
console.log(`length ${(total / 1000).toFixed(1)}s\n`);

const browser = await chromium.launch({ args: ["--force-color-profile=srgb"] });
const context = await browser.newContext({
  viewport: { width: VIEW_W, height: VIEW_H },
  recordVideo: { dir: RAW, size: { width: VIEW_W, height: VIEW_H } },
  reducedMotion: "no-preference", // the merge and the pins must animate
  colorScheme: "light",
  deviceScaleFactor: 1,
});
const page = await context.newPage();

// Applied before first paint so no unzoomed frame is ever recorded.
await page.addInitScript(`
  addEventListener('DOMContentLoaded', () => {
    const s = document.createElement('style');
    s.textContent =
      'html{zoom:${ZOOM};width:${LAYOUT_W}px}';
    document.head.appendChild(s);
  });
`);

await page.goto(SITE, { waitUntil: "networkidle" });
await settle(page);
await prepare(page);
await sleep(900); // a beat of stillness before the clock starts

const t0 = Date.now();
const cues = [];

for (const beat of beats) {
  const start = Date.now() - t0;
  const before = Date.now();
  try {
    await beat.run(page);
  } catch (error) {
    console.error(`  !! beat "${beat.id}" action failed: ${error.message}`);
  }
  // Re-tag after navigation, then re-apply this beat's spotlight.
  if (beat.id === "hero") {
    await prepare(page);
    await spotlight(page, "hero");
  }
  const spent = Date.now() - before;
  const hold = beat.ms - spent;
  if (hold < 0) console.warn(`  !! beat "${beat.id}" overran by ${-hold}ms`);
  await sleep(Math.max(0, hold));

  cues.push({ id: beat.id, startMs: start, ms: beat.ms, on: beat.on, say: beat.say });
  console.log(
    `  ${fmt(start).padEnd(8)} ${beat.id.padEnd(14)} ${(beat.ms / 1000).toFixed(0)}s` +
      (spent > beat.ms ? "  (overran)" : "")
  );
}

await context.close();
await browser.close();

/* ------------------------------------------------------------------ */
/* encode: trim the lead-in so beat 1 is exactly 0:00.0               */
/* ------------------------------------------------------------------ */

const webm = readdirSync(RAW).find((f) => f.endsWith(".webm"));
if (!webm) throw new Error("playwright produced no video");
const src = join(RAW, webm);

const probed = JSON.parse(
  execFileSync("ffprobe", [
    "-v", "error", "-show_entries", "format=duration",
    "-of", "json", src,
  ]).toString()
);
const rawDur = Number(probed.format.duration);
const trim = Math.max(0, rawDur - total / 1000);

console.log(`\nraw ${rawDur.toFixed(2)}s -> trim ${trim.toFixed(2)}s lead-in`);

const mp4 = join(OUT, "divergence-demo.mp4");
execFileSync(
  "ffmpeg",
  [
    "-y", "-i", src,
    "-ss", trim.toFixed(3),
    "-t", (total / 1000).toFixed(3),
    "-an",
    "-c:v", "libx264", "-preset", "slow", "-crf", "20",
    "-pix_fmt", "yuv420p", "-r", "30",
    "-movflags", "+faststart",
    mp4,
  ],
  { stdio: ["ignore", "ignore", "pipe"] }
);

writeFileSync(
  join(OUT, "beats.json"),
  JSON.stringify(
    {
      site: SITE,
      layoutWidth: LAYOUT_W,
      zoom: ZOOM,
      width: VIEW_W,
      height: VIEW_H,
      totalMs: total,
      cues,
    },
    null,
    2
  )
);

const outDur = JSON.parse(
  execFileSync("ffprobe", [
    "-v", "error", "-show_entries", "format=duration,size",
    "-show_entries", "stream=width,height,r_frame_rate,codec_name",
    "-of", "json", mp4,
  ]).toString()
);
console.log(`\n${mp4}`);
console.log(JSON.stringify(outDur, null, 2));

function fmt(ms) {
  const s = ms / 1000;
  return `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, "0")}`;
}
