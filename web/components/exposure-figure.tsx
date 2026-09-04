/**
 * The four-into-one figure — the whole argument in one graphic.
 *
 * Four positions, four asset classes, looks diversified. One hue in four
 * tints, because they are one bet held four ways. Then they merge into a
 * single bar with the combined figure.
 *
 * Full instrument names, not the mockup's abbreviations: the screen and
 * the evidence panel must agree about what a position is called, and the
 * evidence panel is the trust story. spec 007 research.md R3.
 *
 * **This stays a server component.** It does every computation — sorting,
 * formatting, building the sentence — and hands finished strings to
 * `ExposureMerge`, which owns nothing but a boolean. The client boundary
 * sits below the arithmetic on purpose (spec 009 research.md R3).
 */
import type { Finding } from "@/lib/findings";
import { pct } from "@/lib/format";
import { ExposureMerge, type MergeBlock } from "@/components/exposure-merge";

/** One hue, four tints, each with the text colour that clears AA on it.
 *  The mockup sets white on all four; that is 2.25:1 on the lightest.
 *  research.md R6 carries the measurements. */
const TINTS = [
  { bg: "var(--e1)", fg: "var(--on-e1)" },
  { bg: "var(--e2)", fg: "var(--on-e2)" },
  { bg: "var(--e3)", fg: "var(--on-e3)" },
  { bg: "var(--e4)", fg: "var(--on-e4)" },
];

/** Small counts read better as words in a sentence a banker says aloud
 *  (design notes, Copy). Falls back to the digits rather than inventing a
 *  word it does not have. */
const WORDS = [
  "no",
  "one",
  "two",
  "three",
  "four",
  "five",
  "six",
  "seven",
  "eight",
];
const spell = (n: number) => WORDS[n] ?? String(n);

/**
 * What the blocks have in common, in one sentence.
 *
 * Both counts are derived. The previous version read "a worst-of basket
 * on two names he already owns. It is one bet, held four ways" — with
 * "two", "four" and "he" all typed by hand. It renders for five clients
 * and was wrong on three of them, including asserting "he" about a client
 * the book records as a woman. It was right for the demo client, which is
 * why it survived review.
 *
 * **Written with no pronoun at all** rather than by reading the gender
 * column: nothing in this sentence needs to know, and a system that
 * reaches for a pronoun it does not need will eventually get one wrong.
 */
function mergeSentence(members: number, duplicate?: Finding): string {
  const held = `It is one bet, held ${spell(members)} ways.`;
  if (!duplicate) return `One theme, held ${spell(members)} ways.`;

  const names = duplicate.duplicated_instrument_ids?.length ?? 0;
  if (names === 0) return held;

  return (
    `The note references ${spell(names)} ` +
    `${names === 1 ? "name" : "names"} already held outright. ${held}`
  );
}

export function ExposureFigure({
  finding,
  duplicate,
  snapshotDate,
}: {
  finding: Finding;
  duplicate?: Finding;
  snapshotDate: string;
}) {
  const members = [...(finding.members ?? [])].sort((a, b) => b.w - a.w);
  if (members.length === 0) return null;

  const classes = finding.asset_classes ?? [];

  // Everything below is computed here, on the server, and passed down as
  // strings. The merge component receives no Finding and no number.
  const blocks: MergeBlock[] = members.map((position, index) => {
    const tint = TINTS[index % TINTS.length];
    return {
      id: position.instrument_id,
      assetClass: position.asset_class,
      name: position.instrument_name,
      pctLabel: pct(position.w, 1),
      bg: tint.bg,
      fg: tint.fg,
    };
  });

  return (
    <div className="mt-8">
      <div className="mb-3 flex flex-wrap justify-between gap-2 text-[12.5px] text-muted-foreground">
        <span>
          {spell(members.length)} positions. {spell(classes.length)}{" "}
          {classes.length === 1 ? "asset class" : "asset classes"}. Looks
          diversified.
        </span>
        <span className="tabular">{snapshotDate}</span>
      </div>

      <ExposureMerge
        blocks={blocks}
        combinedLabel={pct(finding.theme_pct ?? 0, 1)}
        sentence={mergeSentence(members.length, duplicate)}
        mergedBg="var(--e3)"
        mergedFg="var(--on-e3)"
        barBg="var(--e4)"
        barFg="var(--on-e4)"
        /* "Look through the note" is the line the presenter says — but
           only a client holding a structured product has a note to look
           through. For a plain sector concentration the button has to say
           what it actually does. */
        buttonLabel={
          duplicate ? "Look through the note" : "Show it as one position"
        }
        resetLabel="Reset"
        hint="They were always the same colour. Only the labels differed."
      />

      <p className="mt-4 max-w-[66ch] text-[13px] leading-[1.6] text-muted-foreground">
        {finding.theme} — {finding.headline}
      </p>
    </div>
  );
}

/**
 * The trajectory. A single figure invites "was it always like that?";
 * this answers it.
 */
export function Trajectory({ finding }: { finding: Finding }) {
  const points = finding.trajectory ?? [];
  if (points.length < 2) return null;

  const peak = Math.max(...points.map((p) => p.pct));

  return (
    <div>
      <div className="mb-4 text-[13.5px] text-muted-foreground">
        How it got here. Appreciation through the spring, then a step change
        when the note settled.
      </div>
      <div className="grid h-[120px] grid-cols-5 items-end gap-3 md:h-[120px]">
        {points.map((point, index) => (
          <div key={point.snapshot_date} className="flex h-full flex-col justify-end">
            <div className="font-read mb-1.5 text-center text-[15px] tabular md:text-[17px]">
              {point.pct.toFixed(1)}
            </div>
            <div
              className={`rounded-t-[3px] ${
                index === points.length - 1 ? "bg-e4" : "bg-e2"
              }`}
              style={{ height: `${(point.pct / peak) * 100}%` }}
            />
          </div>
        ))}
      </div>
      <div className="mt-2 grid grid-cols-5 gap-3">
        {points.map((point) => (
          <div
            key={point.snapshot_date}
            className="text-center text-[11px] leading-[1.35] text-muted-foreground tabular"
          >
            {point.snapshot_date}
          </div>
        ))}
      </div>
    </div>
  );
}
