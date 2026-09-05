# Gates

One line per gate, with the time it passed. Article XIV — a gate claimed
but not tagged did not pass.

| Gate | Time | Tag |
|---|---|---|
| G1 — Data | 21:59 | g1 |
| G2 — Findings | 23:43 | g2 |
| G3 — Screens | 00:32 | g3 |
| G4 — Submitted | 14:50 Sat | g4 |

## Repository visibility — Principle XV, recorded honestly

Principle XV reads: *"The repository MUST be public from the first
commit."* **It was not.** The repository was created private and made
public at **10:45 SGT, Saturday 5 September**, after the build was
complete.

The reason was a deliberate decision to keep the work unpublished until
the design was settled, taken at the point the repository was created.
That is a departure from the principle, not a satisfaction of it, and
recording it here is the only thing that keeps the gate log worth
reading — a log that only lists passes is a marketing document.

What the principle was protecting is intact: the commit history is
complete, unrewritten, and now public, so the spec-driven sequence and
every correction along the way can be audited. What was lost is the
ability for anyone to have watched it happen live.

Checked before flipping, since going public exposes the whole history and
not just the current tree: no API key material anywhere in the log, no
tracked `.env` file, `.env.local` gitignored and untracked, and the client
data is the synthetic `SYN-` challenge dataset rather than real client
records.

## Deployment

Production: https://web-aljs-projects.vercel.app
Repository: https://github.com/aljabrialam/alamazing-singhacks-2026 (public)
Demo video: https://youtu.be/q_8llE6ZkaU (2:30)
Pitch deck: deck/out/divergence-deck.pdf · deck/out/divergence-deck.pptx

Static only. There is no backend to deploy — the Python pipeline is a
build-time step and `web/public/findings.json` is committed, so Vercel
serves 25 prerendered pages and nothing runs at demo time. That is the
constitution's Technology Standards, not a shortcut: "No live API between
them."
| G3 — redeployed with spec 008 | 01:17 | — |
