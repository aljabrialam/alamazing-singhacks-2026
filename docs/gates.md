# Gates

One line per gate, with the time it passed. Article XIV — a gate claimed
but not tagged did not pass.

| Gate | Time | Tag |
|---|---|---|
| G1 — Data | 21:59 | g1 |
| G2 — Findings | 23:43 | g2 |
| G3 — Screens | 00:32 | g3 |

## Deployment

Production: https://web-o0k86prrh-aljs-projects.vercel.app

Static only. There is no backend to deploy — the Python pipeline is a
build-time step and `web/public/findings.json` is committed, so Vercel
serves 25 prerendered pages and nothing runs at demo time. That is the
constitution's Technology Standards, not a shortcut: "No live API between
them."
| G3 — redeployed with spec 008 | 01:17 | — |
