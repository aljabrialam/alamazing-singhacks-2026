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
    <div
      className={`jb-rule relative overflow-hidden rounded-[3px] bg-navy px-6 pt-8 text-white md:px-12 md:pt-11 md:pb-10 ${
        /* Room for the figure below the content on a phone — but only
           when there is a figure. Otherwise this is dead space. */
        exposure ? "pb-[150px]" : "pb-8"
      }`}
    >
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
        {client.risk_profile}, {client.service_models.join(", ").toLowerCase()}{" "}
        · {money(client.aum_usd)} · client since {year(client.client_since)}
      </div>

      {/* What they asked us for, quoted. Absent entirely if unrecorded —
          empty quote marks would imply we hold something we do not. */}
      {client.objectives && (
        <div className="mt-7 max-w-[52ch] border-l-2 border-e1/60 pl-[22px]">
          <div className="mb-2 text-[12.5px] text-white/50">
            Their objective, on file since {year(client.client_since)}
          </div>
          <div className="font-read text-[19px] leading-[1.5] text-[#F0EEEA] md:text-[22px]">
            &ldquo;{client.objectives}&rdquo;
          </div>
        </div>
      )}

      {/* The headline figure. Bottom-right on desktop, below the content
          on a phone — reflowed rather than overlapping. Absent when there
          is no look-through finding: no zero, no em-dash. */}
      {exposure && (
        <div className="absolute bottom-7 left-6 text-left md:bottom-10 md:left-auto md:right-12 md:text-right">
          <div className="hero-figure text-e1">
            {pct(exposure.theme_pct ?? 0, 1)}
          </div>
          <div className="mt-2 max-w-[19ch] text-[13px] text-white/60">
            of the portfolio is {exposure.theme}
          </div>
        </div>
      )}

      {/* The date the figures are *as at*. Never today's. */}
      {!exposure && (
        <div className="mt-7 text-[13px] text-white/50 tabular">
          As at {snapshotDate}
        </div>
      )}
    </div>
  );
}
