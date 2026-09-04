/**
 * S1 — the call list. The first and last screen of the demo.
 *
 * Twenty clients ranked by how soon a conversation is worth having, one
 * defensible sentence each — and an explicit count of how many have
 * nothing today.
 *
 * **That absence is a feature.** Block 9: "a system that finds something
 * wrong with everyone gets ignored by Thursday." The count is derived at
 * render time rather than written into the copy, so the sentence cannot
 * drift out of date. research.md R5.
 */
import Link from "next/link";

import { Caption, Sheet } from "@/components/sheet-section";
import {
  findings,
  getClient,
  hasNothingToday,
  nothingTodayCount,
} from "@/lib/findings";
import { money } from "@/lib/format";

export default function CallList() {
  const quiet = nothingTodayCount();
  const total = findings.call_list.length;

  // The clients a brief was written for — the ones worth a conversation
  // this week. Not the same as "clients with any finding at all": ten of
  // twenty have a mandate band outside range, which is real but not all
  // of it is this week's call.
  //
  // Block 9 estimated "sixteen with nothing today". The derived figure is
  // seven, because the mandate and look-through detectors run over the
  // whole book rather than the three demo clients. Stating thirteen
  // "conversations worth having" would be the overstatement block 9
  // warns against, so the heading leads with the briefed clients and the
  // rest of the book is described accurately underneath.
  const briefed = findings.call_list.filter((entry) => entry.has_brief).length;
  const watching = total - quiet - briefed;

  return (
    <div>
      <Caption>This morning</Caption>

      <Sheet>
        <div className="px-6 py-6 md:px-9">
          <h2 className="font-read text-[21px] font-normal">
            {briefed}{" "}
            {briefed === 1 ? "conversation" : "conversations"} worth having
            this week
          </h2>
          <p className="mt-1 max-w-[68ch] text-[13.5px] leading-[1.55] text-muted-foreground">
            {total} clients on the desk. {briefed} with a brief today,{" "}
            {watching} carrying something worth watching, and {quiet} with
            nothing to raise — checked, and clean. Ordered by how soon a
            conversation is worth having, not by size.
          </p>
        </div>

        <ol>
          {findings.call_list.map((entry) => {
            const client = getClient(entry.client_id);
            const nothing = client ? hasNothingToday(client) : true;

            return (
              <li
                key={entry.client_id}
                className="border-t border-hair"
              >
                <Link
                  href={`/client/${entry.client_id}`}
                  className="grid grid-cols-[4px_1fr] items-start gap-4 px-6 py-5 hover:bg-secondary/60 md:grid-cols-[4px_1fr_108px] md:gap-[18px] md:px-9"
                >
                  {/* Colour never carries meaning alone — the row's own
                      text says whether there is anything to raise. */}
                  <span
                    aria-hidden
                    className={`min-h-[46px] w-[4px] self-stretch rounded-[2px] ${
                      nothing ? "bg-hair" : "bg-crest"
                    }`}
                  />

                  <div>
                    <div className="font-read text-[18px] md:text-[19px]">
                      {entry.name}
                    </div>
                    <div className="mt-0.5 text-[12.5px] text-muted-foreground">
                      {client?.risk_profile}
                      {client?.life_stage ? <> · {client.life_stage}</> : null}
                    </div>

                    {entry.why ? (
                      <p
                        className={`font-read mt-2 max-w-[64ch] text-[15px] leading-[1.55] md:text-[16px] ${
                          nothing ? "text-muted-foreground" : "text-prose"
                        }`}
                      >
                        {entry.why}
                      </p>
                    ) : (
                      <p className="font-read mt-2 max-w-[64ch] text-[15px] leading-[1.55] text-muted-foreground md:text-[16px]">
                        Checked. Every band respected and nothing to raise
                        today.
                      </p>
                    )}
                  </div>

                  {/* The AUM column drops below 920px. */}
                  <div className="font-read hidden text-right text-[15px] text-muted-foreground tabular md:block">
                    {money(entry.aum_usd)}
                  </div>
                </Link>
              </li>
            );
          })}
        </ol>
      </Sheet>

      <p className="font-read mt-13 max-w-[70ch] border-t border-hair pt-6 text-[15.5px] leading-[1.68] text-muted-foreground md:text-[16.5px]">
        Every bank checks the portfolio against the mandate. Nobody checks it
        against what the client actually <b className="font-medium text-ink">said</b> —
        so the portfolio at the top of this list passes every control and is
        still the opposite of what he asked for.
      </p>
    </div>
  );
}
