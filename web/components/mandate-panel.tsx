/**
 * The mandate panel. **This carries the argument.**
 *
 * The demo's central claim is that every band is respected and the
 * portfolio is still 42% one bet. That sentence needs the bands on
 * screen — all of them, not just the breaches — which is why the build
 * carries every band rather than only the violations.
 *
 * One of exactly two places boldness is spent (design notes). It is the
 * only boxed element in the brief.
 *
 * The track runs 0–100 rather than scaling each row to its own band.
 * That makes a 0–15 band render narrow and a 40–65 band render wide,
 * which is true and is the point; per-row scaling would make them the
 * same width and flatter the tight one. research.md R4.
 */
import type { ClientRecord } from "@/lib/findings";
import { pct } from "@/lib/format";

export function MandatePanel({ client }: { client: ClientRecord }) {
  const panel = client.mandate_panel;
  const bands = panel.bands;
  if (bands.length === 0) return null;

  const largest = panel.largest_position;

  return (
    <div>
      <div className="mb-5 text-[13.5px] text-muted-foreground">
        Every band in the {bands[0].mandate_code} mandate, against what the
        portfolio actually holds.
      </div>

      <div>
        {bands.map((band) => {
          const breached = band.verdict !== "within";
          const left = Math.max(0, Math.min(100, band.min_pct));
          const width = Math.max(
            0.5,
            Math.min(100, band.max_pct) - left
          );
          const pin = Math.max(0, Math.min(100, band.actual_pct));

          return (
            <div
              key={`${band.portfolio_id}-${band.asset_class}`}
              className="mb-3.5 grid grid-cols-[96px_1fr_54px] items-center gap-2.5 md:grid-cols-[132px_1fr_62px] md:gap-4"
            >
              <div className="text-[12.5px] md:text-[13.5px]">
                {band.asset_class}
              </div>

              <div
                className="relative h-[22px] rounded-[3px] bg-secondary"
                role="img"
                aria-label={`${band.asset_class} ${pct(
                  band.actual_pct
                )}, permitted ${band.min_pct} to ${band.max_pct} per cent, ${
                  breached ? "outside the band" : "within the band"
                }`}
              >
                {/* the permitted range */}
                <div
                  className="absolute inset-y-0 rounded-[3px]"
                  style={{
                    left: `${left}%`,
                    width: `${width}%`,
                    background: breached
                      ? "rgba(164,52,58,.12)"
                      : "rgba(46,107,82,.13)",
                  }}
                />
                {/* where the portfolio actually sits */}
                <div
                  className="absolute -top-[3px] -bottom-[3px] w-[2.5px] rounded-[2px]"
                  style={{
                    left: `calc(${pin}% - 1.25px)`,
                    background: breached
                      ? "var(--crest)"
                      : "var(--safe)",
                  }}
                />
              </div>

              <div className="font-read text-right text-[15px] tabular md:text-[16px]">
                {band.actual_pct.toFixed(1)}
              </div>
            </div>
          );
        })}
      </div>

      {/* The verdict. The tinted block — where the boldness goes. */}
      <div
        className="mt-6 max-w-[62ch] rounded-[4px] px-5 py-4.5"
        style={{
          background: panel.clean
            ? "rgba(46,107,82,.07)"
            : "rgba(164,52,58,.06)",
        }}
      >
        <p className="font-read text-[16px] leading-[1.55] md:text-[17.5px]">
          {panel.clean ? (
            <>
              <b className="font-medium text-safe">
                Every band is respected
              </b>
              {largest && largest.limit_pct !== null ? (
                <>
                  , and the largest position —{" "}
                  {largest.instrument_name} at{" "}
                  {pct(largest.actual_pct, 1)} — sits under its{" "}
                  {largest.limit_pct.toFixed(0)}% limit.
                </>
              ) : (
                "."
              )}{" "}
              Nothing here is a breach, so no control this bank runs would
              raise anything on this portfolio.
            </>
          ) : (
            <>
              <b className="font-medium text-crest">
                {panel.breached_bands.length}{" "}
                {panel.breached_bands.length === 1 ? "band" : "bands"} outside
                range
              </b>
              {panel.breached_positions.length > 0 && (
                <>
                  , and {panel.breached_positions.length}{" "}
                  {panel.breached_positions.length === 1
                    ? "position"
                    : "positions"}{" "}
                  over the concentration limit
                </>
              )}
              .{" "}
              {panel.breached_bands
                .map(
                  (band) =>
                    `${band.asset_class} at ${band.actual_pct.toFixed(
                      2
                    )}% against ${band.min_pct.toFixed(
                      0
                    )}–${band.max_pct.toFixed(0)}`
                )
                .join("; ")}
              .
            </>
          )}
        </p>
      </div>

      {/* Over the limit but exempt from it — the size stays visible, it is
          simply not a violation. */}
      {panel.over_limit_but_exempt.length > 0 && (
        <p className="mt-4 max-w-[64ch] text-[13px] leading-[1.6] text-muted-foreground">
          {panel.over_limit_but_exempt
            .map(
              (position) =>
                `${position.instrument_name} at ${position.actual_pct.toFixed(
                  2
                )}%`
            )
            .join(", ")}{" "}
          {panel.over_limit_but_exempt.length === 1 ? "sits" : "sit"} above the
          single-position limit but{" "}
          {panel.over_limit_but_exempt.length === 1 ? "is" : "are"} diversified
          funds, which the limit does not apply to. Shown because the size
          matters, not because it is a breach.
        </p>
      )}

      {/* Held, not managed. Excluded from the bands, never from view. */}
      {panel.custody.length > 0 && (
        <p className="mt-3 max-w-[64ch] text-[13px] leading-[1.6] text-muted-foreground">
          {panel.custody
            .map((portfolio) => portfolio.portfolio_name)
            .join(", ")}{" "}
          {panel.custody.length === 1 ? "is" : "are"} held on a custody basis
          and not managed to a mandate, so no band applies.
        </p>
      )}
    </div>
  );
}
