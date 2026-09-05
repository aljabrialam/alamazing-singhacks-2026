/**
 * Pitch deck — 8 slides, 1920×1080.
 *
 *   node build.mjs
 *
 * Produces:
 *   out/divergence-deck.pdf        one page per slide, for submission
 *   out/divergence-deck.pptx       image-per-slide, for presenting
 *   out/slides/NN.png              the individual slides
 *
 * Built as HTML and rendered in Chromium rather than authored in
 * PowerPoint, for two reasons:
 *
 *   1. It uses the product's real typefaces and brand values, so the deck
 *      and the workbench cannot drift apart.
 *   2. The PPTX is one full-bleed image per slide. That means **no font
 *      substitution** when presenting from a machine that is not this
 *      one — which is the usual way a deck breaks five minutes before a
 *      pitch. The trade is that the text is not editable in PowerPoint;
 *      edit here and rebuild instead.
 *
 * Every figure on these slides is verified against web/public/findings.json.
 * None of them is typed from memory.
 */
import { chromium } from "playwright";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const OUT = join(import.meta.dirname, "out");
const SLIDES = join(OUT, "slides");
const W = 1920;
const H = 1080;

rmSync(OUT, { recursive: true, force: true });
mkdirSync(SLIDES, { recursive: true });

/* ------------------------------------------------------------------ */

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;1,6..72,400&family=Archivo:wght@400;500;600&display=swap');
:root{
  --navy:#14284B; --deep:#0C1B33; --red:#C8102E;
  --ground:#EAECEF; --sheet:#FFFFFF; --ink:#101821;
  --muted:#6B7280; --hair:#E3E5E8; --safe:#2E6B52;
  --e1:#C9A876; --e2:#B8945B; --e3:#A37F46; --e4:#8A6934;
  --read:'Newsreader',Georgia,serif; --ui:'Archivo',system-ui,sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:${W}px;height:${H}px;overflow:hidden}
body{font-family:var(--ui);color:var(--ink);background:var(--ground);
  -webkit-font-smoothing:antialiased}
.slide{width:${W}px;height:${H}px;position:relative;overflow:hidden;
  background:var(--ground);padding:96px 120px;display:flex;flex-direction:column}
.slide.dark{background:var(--navy);color:#fff}
.slide.mid-v{justify-content:center}
.slide.deep{background:var(--deep);color:#fff}
.topline{position:absolute;left:0;top:0;width:100%;height:8px;background:var(--red)}
.rule{position:absolute;left:0;top:0;bottom:0;width:8px;background:var(--red)}
.wm{position:absolute;right:120px;top:52px;font-size:22px;color:var(--muted);
  letter-spacing:.02em}
.slide.dark .wm,.slide.deep .wm{color:rgba(255,255,255,.45)}
.pg{position:absolute;right:120px;bottom:52px;font-size:22px;color:var(--muted);
  font-variant-numeric:tabular-nums}
.slide.dark .pg,.slide.deep .pg{color:rgba(255,255,255,.4)}
.eyebrow{font-size:26px;color:var(--muted);margin-bottom:18px;letter-spacing:.01em}
.slide.dark .eyebrow,.slide.deep .eyebrow{color:rgba(255,255,255,.55)}
h1{font-family:var(--read);font-size:96px;font-weight:400;line-height:1.02;
  letter-spacing:-.025em}
h2{font-family:var(--read);font-size:64px;font-weight:400;line-height:1.1;
  letter-spacing:-.02em;margin-bottom:30px}
.lede{font-family:var(--read);font-size:38px;line-height:1.45;max-width:34ch;color:#26303C}
.slide.dark .lede,.slide.deep .lede{color:rgba(255,255,255,.82)}
.big{font-family:var(--read);font-size:210px;line-height:.86;color:var(--e1);
  font-variant-numeric:tabular-nums;letter-spacing:-.03em}
.mid{font-family:var(--read);font-size:110px;line-height:.9;
  font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.quote{font-family:var(--read);font-size:52px;line-height:1.35;max-width:30ch}
.tag{display:inline-flex;align-items:center;gap:14px;font-size:24px;
  border:2px solid rgba(200,16,46,.55);color:#F2B8C0;padding:12px 22px;border-radius:3px}
.dot{width:11px;height:11px;border-radius:50%;background:var(--red)}
.grow{flex:1}
.foot{font-size:24px;color:var(--muted);line-height:1.5}
.slide.dark .foot,.slide.deep .foot{color:rgba(255,255,255,.6)}
b{font-weight:500}
.mono{font-family:ui-monospace,Menlo,monospace;font-size:21px;letter-spacing:-.01em}

/* four-into-one */
.four{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:34px}
.four.merged{gap:0}
.blk{padding:26px 24px 30px;border-radius:3px}
.blk .c{font-size:19px;opacity:.8;min-height:26px}
.blk .n{font-size:23px;line-height:1.3;height:92px;margin-top:8px}
.blk .p{font-family:var(--read);font-size:52px;margin-top:12px;
  font-variant-numeric:tabular-nums}
.bar{margin-top:16px;background:var(--e4);color:#fff;border-radius:3px;height:120px;
  display:flex;align-items:center;justify-content:space-between;padding:0 40px}
.bar .l{font-family:var(--read);font-size:34px;max-width:44ch;line-height:1.3}
.bar .r{font-family:var(--read);font-size:76px;font-variant-numeric:tabular-nums}

/* bands */
.brow{display:grid;grid-template-columns:300px 1fr 130px;gap:28px;align-items:center;
  margin-bottom:22px}
.brow .l{font-size:28px}
.track{position:relative;height:38px;background:#F2F3F5;border-radius:3px}
.ok{position:absolute;top:0;bottom:0;background:rgba(46,107,82,.16);border-radius:3px}
.pin{position:absolute;top:-6px;bottom:-6px;width:5px;background:var(--safe);border-radius:2px}
.brow .v{font-family:var(--read);font-size:34px;text-align:right;
  font-variant-numeric:tabular-nums}
.verdict{margin-top:34px;background:rgba(46,107,82,.10);border-left:5px solid var(--safe);
  padding:30px 38px;font-family:var(--read);font-size:36px;line-height:1.4;max-width:52ch}
.verdict b{color:var(--safe)}

/* generic two-column */
.cols{display:grid;grid-template-columns:1fr 1fr;gap:64px;margin-top:12px}
.card{background:var(--sheet);border:1px solid var(--hair);border-radius:3px;padding:34px 38px}
.card h3{font-family:var(--read);font-size:34px;font-weight:400;margin-bottom:14px}
.card p{font-size:25px;line-height:1.5;color:#26303C}
ul{list-style:none}
li{font-size:31px;line-height:1.42;margin-bottom:22px;padding-left:34px;position:relative;
  max-width:40ch}
li::before{content:'';position:absolute;left:0;top:16px;width:14px;height:2px;
  background:var(--red)}
.slide.dark li,.slide.deep li{color:rgba(255,255,255,.86)}
.scells{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-top:34px}
.sc{background:var(--sheet);border:1px solid var(--hair);border-radius:3px;padding:24px}
.sc .k{font-size:20px;color:var(--muted);min-height:56px;line-height:1.3}
.sc .v{font-family:var(--read);font-size:46px;color:var(--red);margin-top:8px;
  font-variant-numeric:tabular-nums}
.sc.tot{background:var(--navy);border-color:var(--navy)}
.sc.tot .k{color:rgba(255,255,255,.7)} .sc.tot .v{color:#fff}
.flow{display:flex;align-items:stretch;gap:0;margin-top:40px}
.step{flex:1;background:var(--sheet);border:1px solid var(--hair);border-radius:3px;
  padding:30px 28px}
.step.g{background:#0F2A22;border-color:#2E6B52;color:#fff}
.step.r{background:#2A1614;border-color:#8B3A34;color:#fff}
.step h4{font-family:var(--read);font-size:30px;font-weight:400;margin-bottom:12px}
.step p{font-size:22px;line-height:1.45;opacity:.85}
.arrow{display:flex;align-items:center;padding:0 16px;font-size:34px;color:var(--muted)}
`;

const wm = `<div class="wm">Julius Bär · Wealth Intelligence</div>`;
const page = (n) => `<div class="pg">${n} / 8</div>`;

/* ------------------------------------------------------------------ */
/* the slides                                                          */
/* ------------------------------------------------------------------ */

const slides = [
  // 1 — title
  {
    id: "01-title",
    note: "Title. The one line, and where to see it working.",
    html: `<div class="slide deep">
      <div class="rule"></div>${wm}${page(1)}
      <div class="eyebrow">ALAMazing · SingHacks 2026</div>
      <h1>Divergence<br/>Engine</h1>
      <div class="lede" style="margin-top:46px;max-width:38ch">
        Every bank checks the portfolio against the mandate.
        <b style="color:var(--e1)">Nobody checks it against what the client
        actually said.</b>
      </div>
      <div class="grow"></div>
      <div class="foot">
        Which client to call first · what is wrong · how to open the conversation<br/>
        <span class="mono">web-aljs-projects.vercel.app</span> &nbsp;·&nbsp;
        <span class="mono">youtu.be/q_8llE6ZkaU</span>
      </div>
    </div>`,
  },

  // 2 — the problem
  {
    id: "02-problem",
    note: "The problem: alarms only fire when a rule breaks.",
    html: `<div class="slide mid-v">
      <div class="topline"></div>${wm}${page(2)}
      <div class="eyebrow">The problem</div>
      <h2>The portfolios worth a<br/>phone call break no rule.</h2>
      <div class="cols" style="grid-template-columns:1.1fr 1fr">
        <div>
          <ul>
            <li>Bank systems raise an alarm when something is <b>against the rules</b>. That catches a lot.</li>
            <li>They cannot catch a portfolio that follows every rule and is still <b>the wrong portfolio for the person who owns it</b>.</li>
            <li>There is no alarm to raise.</li>
          </ul>
        </div>
        <div class="card" style="align-self:start">
          <h3>Priscilla Ong, Asia desk</h3>
          <p><b>20</b> families · USD 8.2m to 87.9m<br/><br/>
          She can properly watch about <b>three</b>.<br/><br/>
          The portfolio that most needs her this morning breaks none of her
          rules.</p>
        </div>
      </div>
    </div>`,
  },

  // 3 — the client and what he asked for
  {
    id: "03-client",
    note: "The client. His objective, in the bank's file since 2014.",
    html: `<div class="slide dark">
      <div class="rule"></div>${wm}${page(3)}
      <span class="tag"><span class="dot"></span> He asked a question on 12 August. It still has no answer.</span>
      <h1 style="font-size:78px;margin-top:34px">Abdullah Al-Mansoori</h1>
      <div class="foot" style="font-size:28px;margin-top:14px">
        49 · Balanced Growth, advisory · USD 32.2m · client since 2014 ·
        Gulf logistics, port services and marine chartering
      </div>
      <div style="margin-top:52px;border-left:4px solid rgba(201,168,118,.65);padding-left:34px">
        <div class="eyebrow" style="margin-bottom:14px">His objective, in the bank's own file since 2014</div>
        <div class="quote">“Build wealth <b style="color:var(--e1)">outside the
        Gulf region</b> and <b style="color:var(--e1)">outside the shipping
        sector</b>; fund a family office in Asia.”</div>
      </div>
      <div class="grow"></div>
      <div class="foot">His business already rises and falls with Gulf shipping.
      He asked for a cushion, not a second copy of the same bet.</div>
    </div>`,
  },

  // 4 — the finding
  {
    id: "04-finding",
    note: "Four holdings, two asset classes, one bet. 42.13%.",
    html: `<div class="slide mid-v">
      <div class="topline"></div>${wm}${page(4)}
      <div class="eyebrow">What he actually holds · as at 26 August 2026</div>
      <h2 style="margin-bottom:6px">Four holdings. Two asset classes.<br/>One bet.</h2>
      <div class="four">
        <div class="blk" style="background:var(--e1);color:var(--ink)">
          <div class="c">Structured Products</div>
          <div class="n">Fixed Coupon Note<br/>ref. Basket C</div>
          <div class="p">12.90%</div></div>
        <div class="blk" style="background:var(--e2);color:var(--ink)">
          <div class="c">Equity</div>
          <div class="n">Pacific Orient<br/>Shipping Ltd</div>
          <div class="p">11.41%</div></div>
        <div class="blk" style="background:var(--e3);color:var(--ink)">
          <div class="c">Equity</div>
          <div class="n">Global Energy<br/>Majors Equity Fund</div>
          <div class="p">8.94%</div></div>
        <div class="blk" style="background:var(--e4);color:#fff">
          <div class="c">Equity</div>
          <div class="n">Asia Pacific Shipping<br/>and Logistics Fund</div>
          <div class="p">8.88%</div></div>
      </div>
      <div class="bar">
        <div class="l">The note's basket references <b>two names already held
        outright</b>. Look through it, and the four are one position.</div>
        <div class="r">42.13%</div>
      </div>
      <div class="foot" style="margin-top:26px">Energy and industrials — against
      an objective of staying out of both. On any report grouped by asset class,
      there are only two groups, so nothing stands out.</div>
    </div>`,
  },

  // 5 — every band respected
  {
    id: "05-compliant",
    note: "The point: every control passes. That is the gap.",
    html: `<div class="slide mid-v">
      <div class="topline"></div>${wm}${page(5)}
      <div class="eyebrow">Against his mandate, today</div>
      <h2>Everything is inside its limits.</h2>
      <div style="margin-top:8px">
        <div class="brow"><div class="l">Equity</div>
          <div class="track"><div class="ok" style="left:40%;right:35%"></div><div class="pin" style="left:58%"></div></div>
          <div class="v">57.97</div></div>
        <div class="brow"><div class="l">Fixed income</div>
          <div class="track"><div class="ok" style="left:15%;right:60%"></div><div class="pin" style="left:15.7%"></div></div>
          <div class="v">15.67</div></div>
        <div class="brow"><div class="l">Structured products</div>
          <div class="track"><div class="ok" style="left:0;right:85%"></div><div class="pin" style="left:12.9%"></div></div>
          <div class="v">12.90</div></div>
        <div class="brow"><div class="l">Alternatives</div>
          <div class="track"><div class="ok" style="left:0;right:75%"></div><div class="pin" style="left:6%"></div></div>
          <div class="v">6.00</div></div>
        <div class="brow"><div class="l">Cash</div>
          <div class="track"><div class="ok" style="left:2%;right:85%"></div><div class="pin" style="left:7.45%"></div></div>
          <div class="v">7.45</div></div>
      </div>
      <div class="verdict"><b>All five bands respected. No single-name breach</b> —
      the largest position is 13.30% against a 15% limit. Nothing the bank
      monitors would raise this, and the portfolio is still 42% one bet.</div>
    </div>`,
  },

  // 6 — the question, answered
  {
    id: "06-scenario",
    note: "His own question, answered. 2.5m on good news.",
    html: `<div class="slide">
      <div class="topline"></div>${wm}${page(6)}
      <div class="eyebrow">His question, from note N-026 · 12 August 2026 — “We have not modelled this.”</div>
      <h2>If the Strait reopens, good news<br/>costs him 2.5 million.</h2>
      <div class="scells">
        <div class="sc"><div class="k">Fixed Coupon Note</div><div class="v">−0.82m</div></div>
        <div class="sc"><div class="k">Pacific Orient Shipping</div><div class="v">−0.73m</div></div>
        <div class="sc"><div class="k">Global Energy Majors</div><div class="v">−0.54m</div></div>
        <div class="sc"><div class="k">Asia Pacific Shipping</div><div class="v">−0.43m</div></div>
        <div class="sc tot"><div class="k">The portfolio</div><div class="v">−7.80%</div></div>
      </div>
      <div class="lede" style="margin-top:40px;max-width:56ch;font-size:34px">
        Brent back from 101.5 to 72.4 — a <b>de-escalation</b>. And in the same
        week calmer shipping lanes mean lower charter rates, so his business
        earns less too. <b>He said so himself</b>, in a note from April.
      </div>
      <div class="grow"></div>
      <div class="foot">The diversification he asked for in 2014 is exactly what
      would have covered this.</div>
    </div>`,
  },

  // 7 — why you can trust it
  {
    id: "07-trust",
    note: "The AI never counts. Evidence on every finding. RM decides.",
    html: `<div class="slide dark">
      <div class="rule"></div>${wm}${page(7)}
      <div class="eyebrow">Why it can be trusted</div>
      <h2 style="color:#fff">The AI reads and writes.<br/>It never counts.</h2>
      <div class="cols" style="grid-template-columns:1fr 1fr;gap:72px">
        <div>
          <ul>
            <li><b>Every figure is ordinary code</b>, not a model. 108 tests, and none of them reads a model output.</li>
            <li><b>Every finding carries its evidence</b> — the file, the row, the value. One that cannot returns nothing.</li>
            <li><b>The AI can be switched off</b> and the numbers do not change.</li>
          </ul>
        </div>
        <div>
          <ul>
            <li><b>The relationship manager decides.</b> Keep, reject, or add a note.</li>
            <li><b>It never contacts a client and never moves money.</b> No code exists that could.</li>
            <li><b>7 of 20 clients are reported as having nothing to raise.</b> A system that flags everyone gets ignored by Thursday.</li>
          </ul>
        </div>
      </div>
      <div class="grow"></div>
      <div class="foot">24 model calls in the whole system, all before anyone
      logs in, all committed with the prompt and settings that produced them.</div>
    </div>`,
  },

  // 8 — running it for real
  {
    id: "08-production",
    note: "Feasibility in one frame, and where the detail lives.",
    html: `<div class="slide">
      <div class="topline"></div>${wm}${page(8)}
      <div class="eyebrow">Running it inside a bank</div>
      <h2>An overnight batch. No live model,<br/>no database, nothing on the wire.</h2>
      <div class="flow">
        <div class="step"><h4>The bank's systems</h4>
          <p>Holdings, mandates, notes, market events. Read-only — there is no
          write path.</p></div>
        <div class="arrow">→</div>
        <div class="step g"><h4>Overnight</h4>
          <p>Ordinary code does all nine checks and every figure. Traced to a
          record.</p></div>
        <div class="arrow">→</div>
        <div class="step r"><h4>AI writes wording</h4>
          <p>Inside the bank's own environment. No name, no account, no figures.
          Switchable off.</p></div>
        <div class="arrow">→</div>
        <div class="step g"><h4>A finished note</h4>
          <p>One file behind the bank's login. An outage still serves
          yesterday's.</p></div>
      </div>
      <div class="cols" style="margin-top:44px;grid-template-columns:1fr 1fr;gap:56px">
        <div class="card"><h3>Built and tested</h3>
          <p>The nine checks · all the arithmetic · the evidence trail · the
          workbench · 53 findings across 20 clients</p></div>
        <div class="card"><h3>Not built</h3>
          <p>Live connections to bank systems · logins and entitlements · the
          security plumbing a bank requires. Known work — and not done.</p></div>
      </div>
      <div class="grow"></div>
      <div class="foot">Hosting on AWS, Google Cloud or Azure · data protection ·
      cost at 100,000 clients · a four-phase rollout where no client's details
      reach a model until phase three &nbsp;→&nbsp;
      <span class="mono">docs/production-feasibility.md</span></div>
    </div>`,
  },
];

/* ------------------------------------------------------------------ */

const PDF_CSS = `
  html,body{height:auto!important;overflow:visible!important}
  .slide{page-break-after:always;break-after:page}
  .slide:last-child{page-break-after:auto;break-after:auto}
`;

/** `pdf` relaxes the single-slide viewport pinning. Without it the eight
 *  slides concatenate inside a 1080px clipped body and the PDF is one
 *  page — which is exactly what happened the first time. */
const doc = (body, pdf = false) =>
  `<!doctype html><html><head><meta charset="utf-8"><style>${CSS}${
    pdf ? PDF_CSS : ""
  }</style></head><body>${body}</body></html>`;

console.log(`rendering ${slides.length} slides at ${W}×${H}…`);

const browser = await chromium.launch();
const page_ = await browser.newPage({
  viewport: { width: W, height: H },
  deviceScaleFactor: 2,
});

const pngs = [];
for (const [i, s] of slides.entries()) {
  await page_.setContent(doc(s.html), { waitUntil: "load" });
  await page_.evaluate(() => document.fonts.ready);
  const file = join(SLIDES, `${s.id}.png`);
  await page_.screenshot({ path: file });
  pngs.push(file);

  // A slide whose content overflows 1080px is silently cropped.
  const over = await page_.evaluate(() => {
    const el = document.querySelector(".slide");
    return el.scrollHeight - el.clientHeight;
  });
  if (over > 0) {
    console.error(`  !! ${s.id} overflows by ${over}px — it would be cropped`);
    process.exitCode = 1;
  } else {
    console.log(`  ok  ${s.id}`);
  }
}

// PDF: one page per slide, exact slide size, no margins.
const pdfPath = join(OUT, "divergence-deck.pdf");
await page_.setContent(doc(slides.map((s) => s.html).join(""), true), {
  waitUntil: "load",
});
await page_.evaluate(() => document.fonts.ready);
await page_.pdf({
  path: pdfPath,
  width: `${W}px`,
  height: `${H}px`,
  printBackground: true,
  pageRanges: `1-${slides.length}`,
  margin: { top: 0, bottom: 0, left: 0, right: 0 },
});

// A one-page PDF means the page breaks did not take. Assert, do not hope.
const pages = (readFileSync(pdfPath).toString("latin1").match(/\/Type\s*\/Page[^s]/g) || []).length;
if (pages !== slides.length) {
  console.error(
    `\n  !! PDF has ${pages} page(s), expected ${slides.length} — page breaks failed`
  );
  process.exitCode = 1;
} else {
  console.log(`  pdf ${pages} pages`);
}

await browser.close();
if (process.exitCode) process.exit(1);

writeFileSync(
  join(OUT, "speaker-notes.md"),
  `# Speaker notes — 3 minutes, 8 slides\n\n` +
    `Roughly 22 seconds a slide. Slides 4 and 5 are the argument; if you are\n` +
    `running long, cut 2 and 7 rather than rushing them.\n\n` +
    slides.map((s, i) => `**${i + 1}. ${s.id}** — ${s.note}`).join("\n\n") +
    "\n"
);

console.log(`\n${join(OUT, "divergence-deck.pdf")}`);
execFileSync("python3", [join(import.meta.dirname, "topptx.py"), ...pngs], {
  stdio: "inherit",
});
