/**
 * The four-into-one figure — the whole argument in one graphic.
 *
 * Four positions, four asset classes, looks diversified. One hue in four
 * tints, because they are one bet held four ways. Then they merge into a
 * single bar with the combined figure.
 *
 * Full instrument names, not the mockup's abbreviations: the screen and
 * the evidence panel must agree about what a position is called, and the
 * evidence panel is the trust story. research.md R3.
 */
import type { Finding } from "@/lib/findings";
import { pct } from "@/lib/format";

const TINTS = ["bg-e1", "bg-e2", "bg-e3", "bg-e4"];

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

  return (
    <div className="mt-8">
      <div className="mb-3 flex flex-wrap justify-between gap-2 text-[12.5px] text-muted-foreground">
        <span>
          {members.length} positions. {classes.length}{" "}
          {classes.length === 1 ? "asset class" : "asset classes"}. Looks
          diversified.
        </span>
        <span className="tabular">{snapshotDate}</span>
      </div>

      <div className="grid grid-cols-2 gap-2.5 md:grid-cols-4">
        {members.map((position, index) => (
          <div
            key={position.instrument_id}
            className={`rounded-[4px] px-3.5 py-3.5 text-white ${
              TINTS[index % TINTS.length]
            }`}
          >
            <div className="min-h-[32px] text-[11.5px] leading-[1.35] opacity-[0.82]">
              {position.instrument_name}
            </div>
            <div className="font-read mt-1.5 text-[24px] tabular">
              {pct(position.w, 1)}
            </div>
            <div className="mt-0.5 text-[11px] opacity-[0.78]">
              {position.asset_class}
            </div>
          </div>
        ))}
      </div>

      <div className="my-3.5 flex justify-center gap-1.5">
        {members.map((position) => (
          <span
            key={position.instrument_id}
            className="h-[22px] w-px bg-hair"
            aria-hidden
          />
        ))}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-5 rounded-[4px] bg-gradient-to-r from-e1 to-e4 px-5 py-4.5 text-white">
        <div className="font-read max-w-[36ch] text-[20px] leading-[1.35]">
          {duplicate
            ? "The note’s underlying is a worst-of basket on two names he already owns. It is one bet, held four ways."
            : `One theme, held ${members.length} ways.`}
        </div>
        <div className="font-read whitespace-nowrap text-[40px] leading-none tabular md:text-[44px]">
          {pct(finding.theme_pct ?? 0, 1)}
        </div>
      </div>

      <p className="mt-3 max-w-[66ch] text-[13px] leading-[1.6] text-muted-foreground">
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
