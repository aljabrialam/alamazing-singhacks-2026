/**
 * The hero. Spec 009, replacing the white identity band.
 *
 * A navy panel with the red rule down its left edge, the objective quoted
 * in a gold-ruled box, and the headline exposure figure set large at the
 * bottom-right. Projector scale: 46px name, 80px figure.
 *
 * A **server** component, so it may hold a `Finding` and call `pct()`.
 * The two client components in this spec deliberately cannot.
 *
 * Every part is optional and absent rather than empty when the data does
 * not support it — no zero where there is no figure, no quote marks
 * around nothing. A placeholder is a small invented claim.
 */
import type { ClientRecord, Finding } from "@/lib/findings";
import { money, pct, shortDate, year } from "@/lib/format";

export function ClientHero({
  client,
  exposure,
  question,
  snapshotDate,
}: {
  client: ClientRecord;
  exposure?: Finding;
  question?: Finding;
  snapshotDate: string;
}) {
  const asked = question?.unanswered_question;

  return (
    <div className="jb-rule overflow-hidden rounded-[3px] bg-navy px-6 py-8 text-white md:px-12 md:py-11">
      {/* Content left, figure bottom-right — as a GRID, not as an
          absolutely positioned figure.

          The mockup positions the figure `absolute; right:48px;
          bottom:38px`, which works there because its quote is one short
          line. Real objectives are not: this client's runs to three lines
          at 22px and ran straight underneath the 80px figure. An absolute
          figure cannot know how tall the text beside it is, so the
          collision is a property of the technique rather than of this
          client — the next long objective would do it again.

          A grid row with `items-end` puts the figure at the bottom of the
          row and reserves its column, so the two can never overlap
          whatever the text length. Stacks on a phone for free. */}
      <div className="grid gap-8 md:grid-cols-[minmax(0,1fr)_auto] md:items-end md:gap-12">
        <div>
          {/* The one crest element on the panel. Text beside the colour,
              never colour alone. */}
          {asked && (
            <span className="inline-flex items-center gap-2.5 rounded-[2px] border border-jb-red/50 px-3.5 py-[7px] text-[13.5px] text-[#F2B8C0]">
              <span
                aria-hidden
                className="h-1.5 w-1.5 rounded-full bg-jb-red"
              />
              {client.name.split(" ")[0]} asked you a question on{" "}
              {shortDate(asked.asked_on)}. It has no answer yet.
            </span>
          )}

          <h2 className={`hero-name ${asked ? "mt-5" : ""} mb-2`}>
            {client.name}
          </h2>

          <div className="text-[14.5px] text-white/60">
            {client.age ? <>{client.age} · </> : null}
            {client.risk_profile},{" "}
            {client.service_models.join(", ").toLowerCase()} ·{" "}
            {money(client.aum_usd)} · client since{" "}
            {year(client.client_since)}
          </div>

          {/* What they asked us for, quoted in full. Absent entirely if
              unrecorded — empty quote marks would imply we hold
              something we do not. Never truncated: the objective is the
              thing the whole finding is measured against. */}
          {client.objectives && (
            <div className="mt-7 max-w-[46ch] border-l-2 border-e1/60 pl-[22px]">
              <div className="mb-2 text-[12.5px] text-white/50">
                Their objective, on file since {year(client.client_since)}
              </div>
              <div className="font-read text-[18px] leading-[1.5] text-[#F0EEEA] md:text-[20px]">
                &ldquo;{client.objectives}&rdquo;
              </div>
            </div>
          )}
        </div>

        {/* The headline figure. Absent when there is no look-through
            finding: no zero, no em-dash, no empty gold slab. */}
        {exposure && (
          <div className="md:text-right">
            <div className="hero-figure whitespace-nowrap text-e1">
              {pct(exposure.theme_pct ?? 0, 1)}
            </div>
            <div className="mt-2 max-w-[20ch] text-[13px] leading-[1.45] text-white/60 md:ml-auto">
              of the portfolio is {exposure.theme}
            </div>
          </div>
        )}
      </div>

      {/* The date the figures are *as at*. Never today's. */}
      {!exposure && (
        <div className="mt-7 text-[13px] text-white/50 tabular">
          As at {snapshotDate}
        </div>
      )}
    </div>
  );
}
