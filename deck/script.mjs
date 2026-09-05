/**
 * The pitch script — a phone-readable PDF.
 *
 *   node script.mjs   →   out/pitch-script.pdf
 *
 * The plan is: say the intro, play the 2:30 video, take questions. So the
 * intro is the only thing that has to be read out, and the budget is
 * unforgiving:
 *
 *     3:00 slot − 2:30 video − ~6s to introduce and click play = 24s
 *     at 150 wpm, unhurried → 60 words
 *
 * The build fails if the intro is over 60 words. Everything after page 2
 * is for the two minutes of questions, which is now the longer half of
 * the slot.
 *
 * 820×1460 portrait: fills a phone screen with no pinch-zooming. Every
 * block is `break-inside: avoid` so nothing splits across a page.
 *
 * Figures match deck/build.mjs, which match web/public/findings.json.
 */
import { chromium } from "playwright";
import { mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const OUT = join(import.meta.dirname, "out");
mkdirSync(OUT, { recursive: true });

const W = 820;
const H = 1460;
const WORD_BUDGET = 60;

/* ------------------------------------------------------------------ */
/* THE INTRO — the only thing you have to say. Read it as written.    */
/* ------------------------------------------------------------------ */

const intro = [
  "Every bank checks a portfolio against the mandate. **Nobody checks it against what the client actually said.**",
  "This client asked us, in 2014, to keep his money **out of Gulf shipping.** Today **forty-two per cent** of it is shipping and energy — and **every control in the bank passes.**",
  "Nothing flags it. Let me show you.",
];

/** One sentence for when the video ends and the room is silent. */
const afterVideo =
  "Every figure in that came from the bank's own records, and the relationship manager decides what to do with it. Happy to take questions.";

/** If the mind goes blank — one sentence, from memory. */
const rescue =
  "This client asked to stay out of shipping. Forty-two per cent of his portfolio is shipping and energy, every single control passes, and so nobody at the bank has noticed.";

const qa = [
  {
    group: "The product",
    items: [
      {
        q: "How is this different from existing risk or compliance tools?",
        a: "Those fire when a rule breaks. This finds the portfolios where **no rule breaks** and it is still wrong. On this client every band passes — that is the point, not a coincidence.",
      },
      {
        q: "Why did nobody at the bank see it?",
        a: "Three reasons. It is spread over four holdings so none looks large. They sit in only **two** asset classes, so a report grouped by asset class shows nothing odd. And one is a structured note whose basket references **two names he already owns** — on paper a fourth investment, in reality the same bet twice.",
      },
      {
        q: "Would a relationship manager actually use it?",
        a: "It gives her three things: who to call first, what is wrong, and a sentence to open with. And **seven of the twenty** clients are reported as having nothing to raise — a system that flags everyone gets ignored by Thursday.",
      },
      {
        q: "What is the business case?",
        a: "One conversation that would not otherwise have happened, with a client holding thirty-two million. The AI costs about **thirteen dollars per client per year** at the ceiling.",
      },
    ],
  },
  {
    group: "The AI",
    items: [
      {
        q: "Can the AI make up a number?",
        a: "No. It never does arithmetic and never produces a figure. Everything is computed in Python and tested — **a hundred and eight tests**, none of which read an AI output. If the AI is wrong you get a clumsy sentence, not a wrong figure.",
      },
      {
        q: "Would compliance allow it?",
        a: "It can be **switched off entirely** and the numbers do not change — the briefs just get plainer. In production it runs inside the bank's own cloud and never sees a client's name or account.",
      },
      {
        q: "How do you stop it hallucinating?",
        a: "Two checks in code, not in the prompt. Any claim whose words are not in the source note is dropped. Any date it cites that is not in the event log is rejected — the file outranks the model.",
      },
      {
        q: "Is it deterministic?",
        a: "Yes. AI output is generated once, committed to disk with the prompt and settings that produced it, and read back. Same inputs, same findings, every run. There is a test for it.",
      },
    ],
  },
  {
    group: "Running it for real",
    items: [
      {
        q: "What is not built?",
        a: "Live connections to bank systems, logins and entitlements, and the security plumbing a bank requires. Known work — and I have not done it. The detection logic and all the arithmetic are built and tested.",
      },
      {
        q: "How would you deploy it?",
        a: "An overnight batch in the bank's own cloud — AWS, Google or Azure — with the model behind a private endpoint. No live model, no database, nothing on the request path. There is a written design for it in the repository.",
      },
      {
        q: "What would you need from the bank?",
        a: "Two things, and I would measure both before promising anything. Whether the instrument data records **what a structured product references** — that gates the whole look-through. And whether relationship managers write down what clients *said*, not only what was decided.",
      },
      {
        q: "Does it scale?",
        a: "It is a batch, parallel by client. At a hundred thousand clients it is roughly **thirteen dollars per client per year**, and most nights far less, because clients whose notes have not changed are skipped.",
      },
    ],
  },
  {
    group: "Scope",
    items: [
      {
        q: "Why this client and not the one in the brief?",
        a: "The brief's own worked example will be demoed by every team. I picked the client where the finding is invisible to every existing control.",
      },
      {
        q: "Does it contact the client, or trade?",
        a: "Never. There is no code that could. It suggests; the relationship manager keeps it, rejects it, or adds a note.",
      },
      {
        q: "Did you use real client data?",
        a: "No — the synthetic dataset from the challenge. Twenty clients, five snapshots.",
      },
    ],
  },
];

const ready = [
  "Video file **open and paused on frame one** — the local file, not a browser tab. Do not rely on the wifi.",
  "Screen mirroring set to **mirror, not extend**, so you can read this phone while they watch the video.",
  "Live app open in a second tab: **web-aljs-projects.vercel.app** — for questions.",
  "Deck open as a third tab, in case the video will not play at all.",
  "The video has **no audio track**. If the room asks about sound, that is by design — the captions carry it.",
];

/* ------------------------------------------------------------------ */

const bold = (t) =>
  t.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\*(.+?)\*/g, "<i>$1</i>");
const words = (t) => t.replace(/\*/g, "").split(/\s+/).filter(Boolean).length;

const introWords = intro.reduce((n, l) => n + words(l), 0);
const introSecs = Math.round((introWords / 150) * 60);
console.log(
  `intro: ${introWords} words ≈ ${introSecs}s   (budget ${WORD_BUDGET} words / 24s)`
);
if (introWords > WORD_BUDGET) {
  console.error(
    `  !! intro is ${introWords - WORD_BUDGET} words over budget — it eats into the video`
  );
  process.exit(1);
}

const html = `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Archivo:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--navy:#14284B;--deep:#0C1B33;--red:#C8102E;--ink:#101821;
  --muted:#6B7280;--hair:#DDE0E4;--safe:#2E6B52;--e1:#C9A876;
  --read:'Newsreader',Georgia,serif;--ui:'Archivo',system-ui,sans-serif}
*{margin:0;padding:0;box-sizing:border-box}
body{width:${W}px;font-family:var(--ui);color:var(--ink);background:#fff;
  -webkit-font-smoothing:antialiased}
.page{width:${W}px;min-height:${H}px;padding:56px 54px 66px;position:relative;
  page-break-after:always;break-after:page;display:flex;flex-direction:column}
.page:last-child{page-break-after:auto;break-after:auto}
.topline{position:absolute;left:0;top:0;width:100%;height:7px;background:var(--red)}
.wm{font-size:21px;color:var(--muted);margin-bottom:22px;letter-spacing:.02em}
.deep{background:var(--deep);color:#fff}
.deep .wm{color:rgba(255,255,255,.5)}

.kicker{font-size:24px;color:var(--e1);font-weight:600;margin-bottom:14px;
  letter-spacing:.06em}
h1{font-family:var(--read);font-size:56px;font-weight:400;line-height:1.06;
  letter-spacing:-.02em;margin-bottom:34px}
p.say{font-family:var(--read);font-size:40px;line-height:1.5;margin-bottom:30px}
p.say b{font-weight:500;background:rgba(201,168,118,.34);padding:0 4px}
.deep p.say b{background:rgba(201,168,118,.22);color:var(--e1)}
.then{margin-top:auto;border-top:2px solid var(--red);padding-top:24px;
  font-size:26px;line-height:1.5}
.then b{font-weight:600}

.clock{display:flex;gap:10px;margin:26px 0 6px}
.cell{flex:1;border:1px solid var(--hair);border-radius:3px;padding:16px 12px;
  text-align:center}
.cell .t{font-family:var(--read);font-size:30px;font-variant-numeric:tabular-nums}
.cell .k{font-size:18px;color:var(--muted);margin-top:4px;line-height:1.35}
.cell.hi{background:var(--navy);border-color:var(--navy);color:#fff}
.cell.hi .k{color:rgba(255,255,255,.72)}

h2{font-family:var(--read);font-size:44px;font-weight:400;margin-bottom:10px;
  letter-spacing:-.015em}
.note{font-size:23px;color:var(--muted);line-height:1.45;margin-bottom:26px;
  font-style:italic}
.panel{background:#F4F6F8;border-left:5px solid var(--navy);padding:28px 30px;
  break-inside:avoid;page-break-inside:avoid;margin-top:28px}
.panel.red{border-left-color:var(--red);background:#FDF3F4}
.panel h3{font-family:var(--read);font-size:32px;font-weight:400;margin-bottom:15px}
.panel p{font-family:var(--read);font-size:29px;line-height:1.55}
.panel p b{font-weight:500;background:rgba(201,168,118,.32);padding:0 3px}
.grp{font-size:21px;color:var(--red);font-weight:600;letter-spacing:.07em;
  text-transform:uppercase;margin:34px 0 18px;padding-bottom:8px;
  border-bottom:2px solid var(--hair)}
.qa{break-inside:avoid;page-break-inside:avoid;margin-bottom:28px}
.qa .q{font-family:var(--read);font-size:28px;line-height:1.38;margin-bottom:10px}
.qa .q::before{content:'Q ';color:var(--red);font-weight:500}
.qa .a{font-size:24px;line-height:1.55;color:#2A3441}
.qa .a::before{content:'A ';color:var(--safe);font-weight:600}
.qa .a b{font-weight:600}
ol{list-style:none;counter-reset:c}
ol li{counter-increment:c;font-size:26px;line-height:1.5;margin-bottom:22px;
  padding-left:46px;position:relative;break-inside:avoid}
ol li::before{content:counter(c);position:absolute;left:0;top:0;
  font-family:var(--read);font-size:28px;color:var(--e1)}
ol li b{font-weight:600}
.pg{position:absolute;right:54px;bottom:26px;font-size:20px;color:var(--muted);
  font-variant-numeric:tabular-nums}
.deep .pg{color:rgba(255,255,255,.4)}
</style></head><body>

<!-- 1 — the intro. The only thing that has to be said. -->
<div class="page deep">
  <div class="wm">SingHacks 2026 · Julius Bär, Wealth Intelligence</div>
  <div class="kicker">SAY THIS — THEN PLAY THE VIDEO</div>
  <h1>Divergence Engine</h1>
  ${intro.map((l) => `<p class="say">${bold(l)}</p>`).join("\n  ")}
  <div class="then">
    <b>→ Now play the video.</b> 2:30. It runs itself — say nothing over it.<br/>
    <span style="color:rgba(255,255,255,.55)">${introWords} words ·
    about ${introSecs} seconds · you have 24.</span>
  </div>
  <div class="pg">1</div>
</div>

<!-- 2 — the plan and the safety nets -->
<div class="page">
  <div class="topline"></div>
  <div class="wm">The three minutes</div>
  <h2>The plan.</h2>
  <div class="clock">
    <div class="cell"><div class="t">0:00</div><div class="k">Intro<br/>~${introSecs}s</div></div>
    <div class="cell hi"><div class="t">0:25</div><div class="k">The video<br/>2:30</div></div>
    <div class="cell"><div class="t">2:55</div><div class="k">One line,<br/>then stop</div></div>
  </div>

  <div class="panel">
    <h3>When the video ends</h3>
    <p>${bold(afterVideo)}</p>
  </div>

  <div class="panel red">
    <h3>If your mind goes blank</h3>
    <p>${bold(rescue)}</p>
    <p style="font-size:24px;margin-top:16px;color:#4A5462">Then play the video.
    It makes the argument without you.</p>
  </div>

  <div class="panel">
    <h3>If you forget a figure</h3>
    <p>Say <b>“about forty per cent”</b>. Never guess a decimal — the exact
    number is <b>42.13%</b>, and it is on screen anyway.</p>
  </div>
  <div class="pg">2</div>
</div>

<!-- 3 — questions -->
<div class="page">
  <div class="topline"></div>
  <div class="wm">Two minutes of questions · the longer half of your slot</div>
  <h2>Q &amp; A</h2>
  <div class="note">One or two sentences, then stop. A short answer invites the
  next question; a long one uses up your two minutes. “I don't know — I'd have
  to check” is a good answer here.</div>
  ${qa
    .map(
      (g) => `<div class="grp">${g.group}</div>
  ${g.items
    .map(
      (x) => `<div class="qa">
    <div class="q">${bold(x.q)}</div>
    <div class="a">${bold(x.a)}</div>
  </div>`
    )
    .join("\n  ")}`
    )
    .join("\n  ")}
</div>

<!-- last — have ready -->
<div class="page">
  <div class="topline"></div>
  <div class="wm">Before you walk up</div>
  <h2>Have this ready.</h2>
  <div class="note">The video is the pitch. Everything here exists to protect it.</div>
  <ol>
    ${ready.map((l) => `<li>${bold(l)}</li>`).join("\n    ")}
  </ol>
  <div class="panel">
    <h3>The one thing to remember</h3>
    <p>You only have to say <b>three sentences</b>. The video does the rest,
    and it cannot forget its lines.</p>
  </div>
</div>

</body></html>`;

/* ------------------------------------------------------------------ */

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H } });
await page.setContent(html, { waitUntil: "load" });
await page.evaluate(() => document.fonts.ready);

const pdf = join(OUT, "pitch-script.pdf");
await page.pdf({
  path: pdf,
  width: `${W}px`,
  height: `${H}px`,
  printBackground: true,
  margin: { top: 0, bottom: 0, left: 0, right: 0 },
});
await browser.close();

// `break-inside: avoid` keeps a question off a page boundary. That cannot
// be checked from the DOM — on screen the document is one continuous flow
// with no page breaks, so measuring against the page height describes a
// layout that does not exist. Verified by rendering the PDF:
//
//   python3 -c "import pypdfium2 as p, pathlib; \
//     pathlib.Path('out/pdfpages').mkdir(exist_ok=True); \
//     d=p.PdfDocument('out/pitch-script.pdf'); \
//     [g.render(scale=.55).to_pil().save(f'out/pdfpages/p{i:02d}.png') \
//      for i,g in enumerate(d,1)]"
const pages = (
  readFileSync(pdf).toString("latin1").match(/\/Type\s*\/Page[^s]/g) || []
).length;
if (pages < 4) {
  console.error(`  !! PDF has ${pages} page(s) — pagination failed`);
  process.exit(1);
}
console.log(`  pdf ${pages} pages`);
console.log(pdf);
