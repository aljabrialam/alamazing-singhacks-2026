# Pitch deck

Eight slides, 1920×1080. Supplementary to the
[demo video](../demo/README.md) — the video carries the walkthrough, this
carries the argument and works as a fallback if the video will not play.

| File | For |
|---|---|
| `out/divergence-deck.pdf` | Submission, and reading. One page per slide. |
| `out/divergence-deck.pptx` | Presenting. |
| `out/speaker-notes.md` | One line per slide, and what to cut if you run long. |
| `out/pitch-script.pdf` | **The words, to read out loud.** Portrait, sized for a phone. |

## Built as HTML, not in PowerPoint

Two reasons, both practical.

It uses the product's own typefaces and brand values, so the deck and the
workbench cannot drift apart — the slides are the same Newsreader, the
same navy, the same red rule.

And **the PPTX is one full-bleed image per slide, so there are no fonts to
substitute.** A deck authored in PowerPoint with Newsreader on it renders
as something else on a machine that does not have Newsreader, which is
the usual way a deck breaks five minutes before a pitch. The cost is that
the text is not editable in PowerPoint: edit `build.mjs` and rebuild.

The build fails if any slide's content overflows 1080px, because an
overflowing slide is silently cropped rather than visibly broken. It also
asserts the PDF has one page per slide — the first build produced a
one-page PDF, because the CSS that pins a single slide to 1080px and hides
overflow clipped eight concatenated slides down to one.

One thing to know about the PDF: Chromium embeds the web fonts as Type3
glyph procedures rather than as named fonts. The upside is that the
lettering travels with the file and renders identically in any viewer.
The downside is that the text is not selectable or searchable. For a deck
that is fine; if a searchable PDF is ever needed, print the PPTX instead.

## Every figure is checked

The figures on these slides come from `web/public/findings.json`, not from
memory: 42.13% across four positions and two asset classes, all five
mandate bands within range, the largest position at 13.30% against a 15%
limit, −2,513,211 and −7.80% on the scenario, 53 findings across 20
clients, 108 tests.

## The read-aloud script

`out/pitch-script.pdf` is 820×1460 — portrait, so it fills a phone screen
with no pinch-zooming, at 31px so it reads at arm's length. Eight pages:
the running order, the script itself, a three-sentence fallback for a
blank moment, and seven likely questions with short answers.

The words in it are meant to be read exactly as written. Key phrases are
highlighted so a lost place can be found in one glance, and every block
is `break-inside: avoid` so a slide's words never split across a page.

The script is checked against 150 words per minute and the build fails
above 3:15. It currently runs **442 words ≈ 2:57**.

## Rebuilding

```bash
cd deck
npm i && npx playwright install chromium
pip3 install python-pptx
node build.mjs      # slides -> pdf + pptx
node script.mjs     # the read-aloud script -> pdf
```
