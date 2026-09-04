/**
 * The loan against the portfolio, over five snapshots.
 *
 * A single reading says *0.59 percentage points from a margin call* — true,
 * and it reads as a fact that might always have been true. The trajectory
 * says he is **moving** toward the trigger, and separates the part he chose
 * from the part that happened to him.
 *
 * specs/008-explanation-collateral-tax-life/research.md R2.
 */
import type { Finding } from "@/lib/findings";
import { exact, shortDate } from "@/lib/format";

export function CollateralTrajectory({ finding }: { finding: Finding }) {
  const facility = finding.facility;
  const trajectory = finding.facility_trajectory;
  const history = facility?.history ?? [];
  if (!facility || !trajectory || history.length < 2) return null;

  const trigger = facility.margin_call_ltv_pct;
  // The track runs 0 to a little past the trigger, so the trigger line
  // sits inside the frame and the gap to it is legible.
  const scale = Math.max(trigger * 1.15, ...history.map((h) => h.ltv_pct) ) ;
  const drawDates = new Set(
    trajectory.balance_changes
      .filter((c) => c.kind === "drawdown")
      .map((c) => c.snapshot_date)
  );

  return (
    <div>
      <h3 className="font-read text-[20px] font-normal">
        The loan against this portfolio
      </h3>
      <p className="mt-2 mb-5 max-w-[62ch] text-[13.5px] leading-[1.55] text-muted-foreground">
        Loan-to-value at every snapshot, against the{" "}
        {trigger.toFixed(0)}% margin-call trigger. A margin call removes the
        client&rsquo;s choice — the bank sells.
      </p>

      <div className="space-y-2.5">
        {history.map((point) => {
          const drew = drawDates.has(point.snapshot_date);
          const near = trigger - point.ltv_pct < 2;
          return (
            <div
              key={point.snapshot_date}
              className="grid grid-cols-[96px_1fr_54px] items-center gap-2.5 md:grid-cols-[132px_1fr_62px] md:gap-4"
            >
              <div className="text-[12.5px] text-muted-foreground tabular md:text-[13px]">
                {shortDate(point.snapshot_date)}
              </div>

              <div
                className="relative h-[22px] rounded-[3px] bg-secondary"
                role="img"
                aria-label={`${point.snapshot_date}: loan-to-value ${point.ltv_pct.toFixed(
                  2
                )} per cent against a ${trigger} per cent trigger${
                  drew ? ", drawn balance increased" : ""
                }`}
              >
                <div
                  className="absolute inset-y-0 left-0 rounded-[3px]"
                  style={{
                    width: `${(point.ltv_pct / scale) * 100}%`,
                    background: near
                      ? "rgba(164,52,58,.55)"
                      : "rgba(46,107,82,.35)",
                  }}
                />
                {/* the trigger */}
                <div
                  className="absolute -top-[3px] -bottom-[3px] w-[2px] bg-crest"
                  style={{ left: `calc(${(trigger / scale) * 100}% - 1px)` }}
                />
              </div>

              <div className="font-read text-right text-[15px] tabular md:text-[16px]">
                {point.ltv_pct.toFixed(2)}
              </div>
            </div>
          );
        })}
      </div>

      {/* What the movement was, told apart by cause. */}
      <div className="mt-6 max-w-[62ch] space-y-3">
        {trajectory.balance_changes
          .filter((change) => change.kind === "drawdown")
          .map((change) => (
            <p
              key={change.snapshot_date}
              className="font-read text-[16px] leading-[1.6] md:text-[17px]"
            >
              On {shortDate(change.snapshot_date)} the drawn balance rose from{" "}
              {exact(change.from)} to {exact(change.to)} {facility.currency}.
              That was <b className="font-medium">a decision</b>, taken while
              the collateral was already falling.
            </p>
          ))}

        {trajectory.collateral_driven_rises.length > 0 && (
          <p className="font-read text-[16px] leading-[1.6] md:text-[17px]">
            Since then <b className="font-medium">nothing further has been
            drawn</b>, and the loan-to-value has still risen{" "}
            {trajectory.collateral_driven_rises
              .reduce((total, rise) => total + rise.ltv_rise_pp, 0)
              .toFixed(2)}{" "}
            percentage points. The collateral is shrinking underneath him —
            and it is the same concentration reported above.
          </p>
        )}

        {trajectory.headroom_lost !== null && (
          <p className="text-[13px] leading-[1.6] text-muted-foreground">
            Borrowing capacity fell by {exact(trajectory.headroom_lost)}{" "}
            {facility.currency} across the five snapshots, from{" "}
            {exact(trajectory.headroom_from ?? 0)} to{" "}
            {exact(trajectory.headroom_to ?? 0)}.{" "}
            {trajectory.pp_to_margin_call.toFixed(2)} percentage points
            remain.
          </p>
        )}
      </div>
    </div>
  );
}
