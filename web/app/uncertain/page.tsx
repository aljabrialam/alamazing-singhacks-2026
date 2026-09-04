/**
 * S3 — what we are not sure about.
 *
 * The brief asks for this explicitly: "if something in the data looks
 * wrong or contradictory, say so in your presentation. Noticing is worth
 * more than quietly working around it."
 *
 * **Two sections, because there are two kinds of not-knowing.** The data
 * imperfections say *the files cannot tell us this*. The method limits say
 * *our approach has this boundary*. Collapsing them into one list would
 * turn the honest thing into a single caveat blob.
 */
import Link from "next/link";

import { Band, Caption, Sheet } from "@/components/sheet-section";
import { findings, getClient } from "@/lib/findings";

export default function Uncertain() {
  const { data_imperfections, method_limits } = findings.uncertainty;

  // Grouped by instrument, because the same gap repeats across snapshots
  // and five identical rows read as noise rather than as one fact.
  const grouped = new Map<
    string,
    { rows: typeof data_imperfections; count: number }
  >();
  for (const imperfection of data_imperfections) {
    const key = `${imperfection.kind}|${imperfection.client_id}|${imperfection.instrument_id}`;
    const existing = grouped.get(key);
    if (existing) {
      existing.count += 1;
    } else {
      grouped.set(key, { rows: [imperfection], count: 1 });
    }
  }

  return (
    <div>
      <Caption>What we are not sure about</Caption>

      <Sheet>
        <Band first>
          <h2 className="font-read text-[21px] font-normal">
            Where the data cannot tell us
          </h2>
          <p className="mt-1 max-w-[64ch] text-[13.5px] leading-[1.55] text-muted-foreground">
            {data_imperfections.length} rows across{" "}
            {grouped.size} {grouped.size === 1 ? "holding" : "holdings"}.
            Nothing here was filled in, repaired or dropped.
          </p>

          <div className="mt-6 space-y-4">
            {[...grouped.values()].map(({ rows, count }) => {
              const first = rows[0];
              const client = getClient(first.client_id);
              return (
                <div
                  key={`${first.kind}-${first.client_id}-${first.instrument_id}`}
                  className="rounded-[4px] border border-hair px-4 py-4"
                >
                  <div className="font-read text-[16px] leading-[1.5]">
                    {first.detail}
                  </div>
                  <div className="font-num mt-2.5 text-[11.5px] leading-[1.6] text-muted-foreground">
                    {first.file} · {first.instrument_id} · {first.field} ·{" "}
                    {count} {count === 1 ? "row" : "rows"}
                  </div>
                  {client && (
                    <div className="mt-2 text-[13px] text-muted-foreground">
                      <Link
                        href={`/client/${first.client_id}`}
                        className="hover:text-ink"
                      >
                        {client.name}
                      </Link>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Band>

        <Band>
          <h2 className="font-read text-[21px] font-normal">
            Where our method has a limit
          </h2>
          <p className="mt-1 max-w-[64ch] text-[13.5px] leading-[1.55] text-muted-foreground">
            {method_limits.length} findings carry something we would check
            before relying on them. This is what we would check.
          </p>

          <div className="mt-6 space-y-4">
            {method_limits.map((limit, index) => {
              const client = getClient(limit.client_id);
              return (
                <div
                  key={`${limit.client_id}-${index}`}
                  className="rounded-[4px] border border-hair px-4 py-4"
                >
                  <div className="font-read text-[15px] leading-[1.45] text-muted-foreground">
                    {limit.headline}
                  </div>
                  <div className="font-read mt-2 max-w-[70ch] text-[16px] leading-[1.6]">
                    {limit.unsure_about}
                  </div>
                  {client && (
                    <div className="mt-2.5 text-[13px] text-muted-foreground">
                      <Link
                        href={`/client/${limit.client_id}`}
                        className="hover:text-ink"
                      >
                        {client.name}
                      </Link>{" "}
                      · {limit.kind}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Band>
      </Sheet>

      <p className="font-read mt-13 max-w-[70ch] border-t border-hair pt-6 text-[15.5px] leading-[1.68] text-muted-foreground md:text-[16.5px]">
        A private-market valuation that lags a quarter is industry practice,
        not an error, and is shown here as a lag rather than a defect. The
        distinction matters: a system that cries wolf about its own inputs
        gets switched off.
      </p>
    </div>
  );
}
