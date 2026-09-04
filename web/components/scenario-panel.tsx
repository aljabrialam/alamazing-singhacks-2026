/**
 * The scenario panel — the answer to the question he actually asked.
 *
 * He is not asking about a crash. He is asking about good news: a
 * de-escalation, the world calming down. The answer is that good news
 * costs him money in the portfolio *and* in the business, in the same
 * week. That asymmetry is the reason he cannot wait, so the panel leads
 * with the question and ends with the second-order effect.
 */
import type { Finding } from "@/lib/findings";
import { pct, shortDate, signedMillions } from "@/lib/format";

export function ScenarioPanel({
  finding,
  question,
}: {
  finding: Finding;
  question?: Finding;
}) {
  const scenario = finding.scenario;
  const positions = [...(finding.positions ?? [])].sort(
    (a, b) => a.impact_usd - b.impact_usd
  );
  if (!scenario || positions.length === 0) return null;

  return (
    <div>
      <h3 className="font-read text-[20px] font-normal">
        If {scenario.series_name} returns to where it was
      </h3>

      {/* His own question, in the note's words. */}
      {question?.unanswered_question && (
        <p className="font-read mt-2 mb-5 max-w-[60ch] text-[16px] italic leading-[1.55] text-muted-foreground">
          He asked on {shortDate(question.unanswered_question.asked_on)}, and
          the note records that it was not answered.
        </p>
      )}

      <div className="mb-5 text-[13px] text-muted-foreground tabular">
        {scenario.series_name} {scenario.value_now} → {scenario.value_then}{" "}
        {scenario.unit} · repriced to {shortDate(scenario.date_then)}
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-[repeat(auto-fit,minmax(118px,1fr))]">
        {positions.map((position) => (
          <div
            key={position.instrument_id}
            className="rounded-[4px] border border-hair px-3.5 py-3.5"
          >
            <div className="min-h-[30px] text-[12px] leading-[1.35] text-muted-foreground">
              {position.instrument_name}
            </div>
            <div className="font-read mt-1 text-[21px] text-crest tabular">
              {signedMillions(position.impact_usd)}
            </div>
            <div className="mt-0.5 text-[11px] text-muted-foreground tabular">
              {(position.value_now_usd / 1_000_000).toFixed(2)}m →{" "}
              {(position.value_then_usd / 1_000_000).toFixed(2)}m
            </div>
          </div>
        ))}

        <div className="rounded-[4px] border border-navy bg-navy px-3.5 py-3.5">
          <div className="min-h-[30px] text-[12px] leading-[1.35] text-white/[0.72]">
            Total, on a de-escalation
          </div>
          <div className="font-read mt-1 text-[21px] text-white tabular">
            {signedMillions(finding.total_impact_usd ?? 0)}
          </div>
          <div className="mt-0.5 text-[11px] text-white/[0.72] tabular">
            {pct(finding.total_impact_pct ?? 0)} of the portfolio
          </div>
        </div>
      </div>

      {/* The second-order effect. His words, not our inference. */}
      {finding.second_order && finding.second_order.notes.length > 0 && (
        <p className="font-read mt-6 max-w-[62ch] text-[16px] leading-[1.6] md:text-[17.5px]">
          The same event reaches this client twice. Their wealth comes from{" "}
          {finding.second_order.source_of_wealth.replace(
            /^Entrepreneur - /,
            ""
          )}
          , and in note {finding.second_order.notes[0].note_id} the client said so
          directly — that their operating business benefits from the same
          conditions, and that the point of this portfolio was to be
          uncorrelated with it. A de-escalation takes value from the
          portfolio and from the business in the same week.
        </p>
      )}
    </div>
  );
}
