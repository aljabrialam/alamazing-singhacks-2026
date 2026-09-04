/**
 * What the portfolio did, and why. Building Block 1 of the brief.
 *
 * Three buckets, never one number. A single "portfolio change" figure
 * would say the market gave this client six million; 3.8m of it is money
 * he paid in. The separation is the point of the panel, so it leads with
 * it rather than burying it under a list of movers.
 */
import type { Finding } from "@/lib/findings";
import { shortDate, signedMillions } from "@/lib/format";

export function ExplanationPanel({ finding }: { finding: Finding }) {
  const held = finding.held ?? [];
  const acquired = finding.acquired ?? [];
  const paidIn = finding.paid_in_usd ?? 0;
  const market = finding.market_movement_usd ?? 0;
  const total = finding.total_change_usd ?? 0;
  if (!finding.window) return null;

  return (
    <div>
      <h3 className="font-read text-[20px] font-normal">
        What the portfolio did since {shortDate(finding.window.from)}
      </h3>

      {/* The separation, before any figure is attributed to skill. */}
      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-[4px] border border-hair px-4 py-3.5">
          <div className="min-h-[30px] text-[12px] leading-[1.35] text-muted-foreground">
            Market movement, on positions held throughout
          </div>
          <div className="font-read mt-1 text-[21px] tabular">
            {signedMillions(market)}
          </div>
        </div>

        {paidIn > 0 && (
          <div className="rounded-[4px] border border-hair px-4 py-3.5">
            <div className="min-h-[30px] text-[12px] leading-[1.35] text-muted-foreground">
              Money paid in — <b className="font-medium">not performance</b>
            </div>
            <div className="font-read mt-1 text-[21px] tabular">
              {signedMillions(paidIn)}
            </div>
          </div>
        )}

        <div className="rounded-[4px] border border-navy bg-navy px-4 py-3.5">
          <div className="min-h-[30px] text-[12px] leading-[1.35] text-white/[0.72]">
            Total change in the portfolio
          </div>
          <div className="font-read mt-1 text-[21px] text-white tabular">
            {signedMillions(total)}
          </div>
        </div>
      </div>

      {acquired.length > 0 && (
        <p className="font-read mt-5 max-w-[62ch] text-[16px] leading-[1.6] md:text-[17px]">
          {acquired.map((entry) => (
            <span key={entry.instrument_id}>
              {entry.instrument_name} was subscribed inside this window —{" "}
              {((entry.paid_in_usd ?? 0) / 1_000_000).toFixed(2)}m paid in,
              now worth {(entry.value_now_usd / 1_000_000).toFixed(2)}m. The{" "}
              {signedMillions(entry.change_usd)} it adds to the portfolio is
              almost all the subscription, not a gain.
            </span>
          ))}
        </p>
      )}

      {held.length > 0 && (
        <div className="mt-5">
          <div className="mb-2.5 text-[13px] text-muted-foreground">
            What actually moved
          </div>
          <div className="space-y-1.5">
            {held
              .slice()
              .sort((a, b) => Math.abs(b.change_usd) - Math.abs(a.change_usd))
              .map((entry) => (
                <div
                  key={entry.instrument_id}
                  className="grid grid-cols-[1fr_80px] items-baseline gap-3"
                >
                  <div className="font-read text-[15px] leading-[1.4] md:text-[16px]">
                    {entry.instrument_name}
                  </div>
                  <div
                    className={`font-read text-right text-[15px] tabular md:text-[16px] ${
                      entry.change_usd < 0 ? "text-crest" : ""
                    }`}
                  >
                    {signedMillions(entry.change_usd)}
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {finding.events.length > 0 && (
        <p className="mt-5 max-w-[64ch] text-[13px] leading-[1.6] text-muted-foreground">
          Events touching this client in the window, from the bank&rsquo;s own
          event log: {finding.events.join(", ")}. The attribution above is
          arithmetic; the causal link is a keyword match and is stated as
          such.
        </p>
      )}
    </div>
  );
}
