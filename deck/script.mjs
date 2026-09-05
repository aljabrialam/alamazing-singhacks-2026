/**
 * The read-aloud script, as a phone-readable PDF.
 *
 *   node script.mjs   →   out/pitch-script.pdf
 *
 * Sized 820×1460 so it fills a phone screen in portrait with no
 * pinch-zooming, and set at 30px so it is readable at arm's length under
 * stage lights. Every block is `break-inside: avoid`, so a slide's words
 * never split across two pages — the point of this document is that you
 * can lose your place and find it again in one glance.
 *
 * Figures in the script match deck/build.mjs, which matches
 * web/public/findings.json. Say them as written.
 */
import { chromium } from "playwright";
import { mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const OUT = join(import.meta.dirname, "out");
mkdirSync(OUT, { recursive: true });

const W = 820;
const H = 1460;

/* ------------------------------------------------------------------ */
/* the script. `say` is read verbatim. Timings are cumulative.         */
/* ------------------------------------------------------------------ */

const beats = [
  {
    n: 1,
    at: "0:00",
    slide: "Title — Divergence Engine",
    say: [
      "Good evening.",
      "Every bank checks a portfolio against the mandate. **Nobody checks it against what the client actually said.**",
      "I'll show you one client where those two things are opposites — and every control in the bank says he is fine.",
    ],
  },
  {
    n: 2,
    at: "0:20",
    slide: "The problem",
    say: [
      "Bank systems raise an alarm when a rule is broken. That works.",
      "What they cannot catch is a portfolio that follows **every** rule and is still the wrong portfolio for the person who owns it — because there is no alarm to raise.",
      "Priscilla here looks after **twenty** families. She can properly watch about **three**.",
    ],
  },
  {
    n: 3,
    at: "0:42",
    slide: "Abdullah Al-Mansoori",
    say: [
      "Abdullah Al-Mansoori made his money in Gulf shipping — ports, cargo, chartering vessels.",
      "When he opened his account in **2014** he asked for one thing, and the bank wrote it down: build wealth **outside the Gulf, and outside shipping.**",
      "His business already rises and falls with Gulf shipping. He wanted a cushion — not a second copy of the same bet.",
    ],
  },
  {
    n: 4,
    at: "1:04",
    slide: "Four holdings. Two asset classes. One bet.",
    say: [
      "Today, **forty-two per cent** of his portfolio is shipping and energy.",
      "It hides because it is four separate holdings, sitting in only **two** asset classes. And one of them is a structured note whose basket references **two companies he already owns outright.**",
      "So it looks like a fourth investment. It is the same bet, bought twice.",
      "Look through it, and it is **forty-two point one three per cent.**",
    ],
  },
  {
    n: 5,
    at: "1:32",
    slide: "Everything is inside its limits",
    key: true,
    say: [
      "Here is the part that matters.",
      "**Every mandate band is respected.** His largest position is thirteen point three per cent, against a fifteen per cent limit. There is no breach anywhere.",
      "**Nothing in the bank's monitoring would ever raise this.**",
      "That gap — between compliant, and what the client actually asked for — is the whole product.",
    ],
  },
  {
    n: 6,
    at: "2:00",
    slide: "If the Strait reopens",
    say: [
      "And it is urgent.",
      "On the **twelfth of August** he asked what happens if the Middle East calms down. The note in the file says: **we have not modelled this.** Nobody got back to him.",
      "So we did. If oil returns to pre-conflict levels he loses about **two and a half million** — **on good news.** And his charter rates fall in the same week.",
    ],
  },
  {
    n: 7,
    at: "2:24",
    slide: "The AI reads and writes. It never counts.",
    say: [
      "On trust. The AI reads and writes — **it never counts.**",
      "Every figure is ordinary code. **A hundred and eight tests**, and not one of them reads an AI output.",
      "Every finding carries the file and the row it came from. And **Priscilla decides** — the system never contacts a client, and never moves money.",
    ],
  },
  {
    n: 8,
    at: "2:44",
    slide: "Running it inside a bank",
    say: [
      "It runs as an overnight batch. No live model, no database.",
      "And **seven of the twenty** clients are reported as having nothing to raise — because a system that finds something wrong with everyone gets ignored by Thursday.",
      "Thank you.",
    ],
  },
];

/* If the mind goes blank — three sentences, from memory, any slide. */
const rescue = [
  "Every bank checks the portfolio against the mandate. Nobody checks it against what the client **said**.",
  "This client asked to stay out of Gulf shipping. Forty-two per cent of his portfolio is shipping and energy — and **every single control passes.**",
  "We find that, show the records it came from, and hand the banker a sentence to open the call.",
];

const qa = [
  {
    q: "How is this different from existing risk or compliance tools?",
    a: "Those fire when a rule breaks. This one finds the portfolios where **no rule breaks** and it is still wrong. On this client every band passes — that is the point, not a coincidence.",
  },
  {
    q: "Can the AI make up a number?",
    a: "No. It never sees arithmetic and never produces one. Every figure is computed in Python and tested. If the AI is wrong you get a clumsy sentence, not a wrong figure.",
  },
  {
    q: "Would a bank's compliance team allow the AI?",
    a: "It can be switched off entirely and the numbers do not change — briefs just get plainer. In production it runs inside the bank's own cloud, and never sees a client's name or account.",
  },
  {
    q: "What if the relationship manager's notes are poor?",
    a: "Then the notes detector gets nothing, and I would say so rather than pretend. That is change management, not engineering. The look-through and the scenario need no notes at all — they would go live first.",
  },
  {
    q: "Does it scale?",
    a: "It is an overnight batch, parallel by client. At a hundred thousand clients the AI cost is roughly **thirteen dollars per client per year** at the ceiling, and most nights it is far less because unchanged clients are skipped.",
  },
  {
    q: "What is not built?",
    a: "The live connections to bank systems, logins, and the security plumbing a bank requires. Known work — and I have not done it. The detection logic and all the arithmetic are built and tested.",
  },
  {
    q: "Why this client and not the one in the brief?",
    a: "The brief's own worked example will be demoed by every team. I picked the client where the finding is invisible to every existing control.",
  },
];

/* ------------------------------------------------------------------ */

const bold = (t) => t.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");

const html = `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Archivo:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--navy:#14284B;--deep:#0C1B33;--red:#C8102E;--ink:#101821;
  --muted:#6B7280;--hair:#DDE0E4;--safe:#2E6B52;--e1:#C9A876;
  --read:'Newsreader',Georgia,serif;--ui:'Archivo',system-ui,sans-serif}
*{margin:0;padding:0;box-sizing:border-box}
body{width:${W}px;font-family:var(--ui);color:var(--ink);background:#fff;
  -webkit-font-smoothing:antialiased}
.page{width:${W}px;min-height:${H}px;padding:60px 56px 70px;position:relative;
  page-break-after:always;break-after:page}
.page:last-child{page-break-after:auto;break-after:auto}
.topline{position:absolute;left:0;top:0;width:100%;height:7px;background:var(--red)}

/* cover */
.cover{background:var(--deep);color:#fff}
.cover .kicker{font-size:24px;color:rgba(255,255,255,.55);margin-bottom:20px}
.cover h1{font-family:var(--read);font-size:76px;font-weight:400;line-height:1.03;
  letter-spacing:-.02em}
.cover .sub{font-family:var(--read);font-size:32px;line-height:1.45;
  color:rgba(255,255,255,.8);margin-top:34px}
.plan{margin-top:46px;border-top:1px solid rgba(255,255,255,.18);padding-top:26px}
.plan div{display:flex;justify-content:space-between;font-size:25px;
  padding:11px 0;color:rgba(255,255,255,.78);border-bottom:1px solid rgba(255,255,255,.08)}
.plan b{font-weight:500;color:#fff}
.tip{margin-top:40px;border-left:4px solid var(--e1);padding-left:22px;
  font-family:var(--read);font-size:27px;line-height:1.5;color:rgba(255,255,255,.85)}

h2{font-family:var(--read);font-size:44px;font-weight:400;margin-bottom:8px;
  letter-spacing:-.015em}
.beat{break-inside:avoid;page-break-inside:avoid;margin-bottom:52px}
.hdr{display:flex;align-items:baseline;gap:18px;border-bottom:2px solid var(--hair);
  padding-bottom:14px;margin-bottom:26px}
.num{font-family:var(--read);font-size:52px;color:var(--e1);line-height:1;
  min-width:56px}
.at{font-size:26px;color:var(--red);font-variant-numeric:tabular-nums;font-weight:500}
.on{font-size:23px;color:var(--muted);line-height:1.35}
.beat.key .hdr{border-bottom-color:var(--red)}
.beat.key .num{color:var(--red)}
p.say{font-family:var(--read);font-size:31px;line-height:1.58;margin-bottom:22px}
p.say b{font-weight:500;background:rgba(201,168,118,.28);padding:0 3px}
.pause{font-size:22px;color:var(--muted);font-style:italic;margin:-8px 0 22px}

.panel{background:#F4F6F8;border-left:5px solid var(--navy);padding:32px 34px;
  break-inside:avoid}
.panel.red{border-left-color:var(--red);background:#FDF3F4}
.panel h3{font-family:var(--read);font-size:36px;font-weight:400;margin-bottom:18px}
.panel p{font-family:var(--read);font-size:30px;line-height:1.55;margin-bottom:18px}
.panel p:last-child{margin-bottom:0}
.panel p b{font-weight:500;background:rgba(201,168,118,.3);padding:0 3px}

.qa{break-inside:avoid;page-break-inside:avoid;margin-bottom:40px;
  border-bottom:1px solid var(--hair);padding-bottom:32px}
.qa .q{font-family:var(--read);font-size:31px;line-height:1.4;margin-bottom:14px}
.qa .q::before{content:'Q  ';color:var(--red);font-weight:500}
.qa .a{font-size:26px;line-height:1.55;color:#2A3441}
.qa .a::before{content:'A  ';color:var(--safe);font-weight:600}
.qa .a b{font-weight:600}
.pg{position:absolute;right:56px;bottom:30px;font-size:21px;color:var(--muted);
  font-variant-numeric:tabular-nums}
.cover .pg{color:rgba(255,255,255,.4)}
.wm{font-size:21px;color:var(--muted);margin-bottom:26px;letter-spacing:.02em}
</style></head><body>

<!-- cover -->
<div class="page cover">
  <div class="kicker">SingHacks 2026 · Julius Bär, Wealth Intelligence</div>
  <h1>Read this<br/>out loud.</h1>
  <div class="sub">Three minutes, eight slides. The words are written to be
  read exactly as they are. If you lose your place, the <b>highlighted</b>
  words are the ones that matter.</div>
  <div class="plan">
    ${beats
      .map(
        (b) =>
          `<div><span><b>${b.n}</b> &nbsp; ${b.slide}</span><span>${b.at}</span></div>`
      )
      .join("\n    ")}
    <div><span>Q &amp; A</span><span>2:00</span></div>
  </div>
  <div class="tip">Slides <b>4</b> and <b>5</b> are the argument. If you are
  running long, hurry slides 2 and 7 — never those two.</div>
  <div class="pg">1</div>
</div>

<!-- the script -->
<div class="page">
  <div class="topline"></div>
  <div class="wm">The script · read verbatim</div>
  ${beats
    .map(
      (b) => `<div class="beat${b.key ? " key" : ""}">
    <div class="hdr">
      <div class="num">${b.n}</div>
      <div>
        <div class="at">${b.at}</div>
        <div class="on">Slide: ${b.slide}</div>
      </div>
    </div>
    ${b.say.map((l) => `<p class="say">${bold(l)}</p>`).join("\n    ")}
  </div>`
    )
    .join("\n  ")}
</div>

<!-- rescue -->
<div class="page">
  <div class="topline"></div>
  <div class="wm">If your mind goes blank</div>
  <h2>Say these three things.</h2>
  <p class="pause">Any slide, any order. This is the whole pitch. Then stop
  and ask if they would like the detail.</p>
  <div class="panel red">
    ${rescue.map((l) => `<p>${bold(l)}</p>`).join("\n    ")}
  </div>
  <div style="margin-top:46px" class="panel">
    <h3>And if you forget a number</h3>
    <p>Say <b>“about forty per cent”</b> rather than guess a decimal. The
    exact figure is on the slide behind you, and the judges can read it.</p>
    <p>Never invent a figure you are not sure of. <b>“It is on the slide —
    forty-two point one three”</b> is a fine thing to say.</p>
  </div>
</div>

<!-- Q&A -->
<div class="page">
  <div class="topline"></div>
  <div class="wm">Two minutes of questions · short answers</div>
  <h2>Q &amp; A</h2>
  <p class="pause">Answer in one or two sentences, then stop. A short answer
  invites the next question; a long one uses your two minutes.</p>
  <div style="margin-top:30px">
    ${qa
      .map(
        (x) => `<div class="qa">
      <div class="q">${bold(x.q)}</div>
      <div class="a">${bold(x.a)}</div>
    </div>`
      )
      .join("\n    ")}
  </div>
  <div class="panel" style="margin-top:10px">
    <h3>If you do not know</h3>
    <p><b>“I don't know — I'd have to check.”</b> That is a good answer here.
    The whole project is built on not inventing figures, so saying it out
    loud is consistent, not weak.</p>
  </div>
</div>

</body></html>`;

/* ------------------------------------------------------------------ */

const words = beats.flatMap((b) => b.say).join(" ").replace(/\*\*/g, "");
const count = words.split(/\s+/).length;
const secs = Math.round((count / 150) * 60); // 150 wpm, unhurried

console.log(`script: ${count} words ≈ ${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")} at 150 wpm`);
if (secs > 195) {
  console.error(`  !! over three minutes with no margin — trim the script`);
  process.exitCode = 1;
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H } });
await page.setContent(html, { waitUntil: "load" });
await page.evaluate(() => document.fonts.ready);

// Optional visual check: SHOT_PAGES=1 writes one PNG per page so the
// page breaks can be inspected. A beat split across two pages defeats the
// purpose of the document.
if (process.env.SHOT_PAGES) {
  const pages = await page.$$(".page");
  for (const [i, el] of pages.entries()) {
    await el.screenshot({ path: join(OUT, `script-p${i + 1}.png`) });
  }
  console.log(`  wrote ${pages.length} page PNGs`);
}

const pdf = join(OUT, "pitch-script.pdf");
await page.pdf({
  path: pdf,
  width: `${W}px`,
  height: `${H}px`,
  printBackground: true,
  margin: { top: 0, bottom: 0, left: 0, right: 0 },
});
await browser.close();

// `break-inside: avoid` on .beat and .qa keeps a block off a page
// boundary. That cannot be checked from the DOM — on screen the document
// is one continuous flow with no page breaks, so measuring against the
// page height reports splits that the paged output does not have. It is
// verified by rendering the PDF:
//
//   python3 -c "import pypdfium2 as p, pathlib; d=p.PdfDocument('out/pitch-script.pdf'); \
//     [pg.render(scale=.55).to_pil().save(f'out/pdfpages/p{i:02d}.png') for i,pg in enumerate(d,1)]"
//
// Last checked: 8 pages, no beat or question split across a break.
const pages = (readFileSync(pdf).toString("latin1").match(/\/Type\s*\/Page[^s]/g) || []).length;
if (pages < 4) {
  console.error(`  !! PDF has ${pages} page(s) — pagination failed`);
  process.exit(1);
}
console.log(`  pdf ${pages} pages`);

if (process.exitCode) process.exit(1);
console.log(pdf);
