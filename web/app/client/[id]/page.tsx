/**
 * S2 — the brief. **The demo.**
 *
 * A document, not a dashboard. Eight sections in block 9's order:
 *
 *   1. Name, age, mandate, AUM
 *   2. The client's objective, quoted
 *   3. Three or four paragraphs of brief, in serif
 *   4. THE MANDATE PANEL — every band, and the verdict
 *   5. THE SCENARIO PANEL
 *   6. The opening line, large, navy
 *   7. Keep / Not useful / Add a note
 *   8. Evidence, always visible on desktop
 *
 * Items 4 and 6 are the two things a judge remembers. Everything else is
 * deliberately quiet.
 */
import Link from "next/link";
import { notFound } from "next/navigation";

import { Band, Caption, Sheet } from "@/components/sheet-section";
import { CollateralTrajectory } from "@/components/collateral-trajectory";
import { Decisions } from "@/components/decisions";
import { EvidenceColumn } from "@/components/evidence";
import { ExplanationPanel } from "@/components/explanation-panel";
import { ExposureFigure, Trajectory } from "@/components/exposure-figure";
import { MandatePanel } from "@/components/mandate-panel";
import { ScenarioPanel } from "@/components/scenario-panel";
import {
  clientIds,
  duplicateUnderlying,
  findings,
  getClient,
  lookThrough,
  openQuestion,
  explanation,
  profileMismatch,
  saidVsHeld,
  scenario,
  taxPosition,
} from "@/lib/findings";
import { money, shortDate, year } from "@/lib/format";

export function generateStaticParams() {
  return clientIds().map((id) => ({ id }));
}

export default async function ClientBrief({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const client = getClient(id);
  if (!client) notFound();

  const exposure = lookThrough(client);
  const duplicate = duplicateUnderlying(client);
  const said = saidVsHeld(client);
  const question = openQuestion(client);
  const repricing = scenario(client);
  const explained = explanation(client);
  const tax = taxPosition(client);
  const profile = profileMismatch(client);
  const runway = client.findings.filter((f) => f.kind === "D4");
  const snapshot = findings.meta.snapshot_date;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_336px] lg:gap-7">
      <div>
        <Caption>The brief</Caption>

        <Sheet>
          {/* 1 — who he is */}
          <Band first>
            <div className="flex flex-wrap items-baseline justify-between gap-5">
              <h2 className="font-read text-[26px] font-normal tracking-[-0.015em] md:text-[32px]">
                {client.name}
              </h2>
              <div className="text-[13.5px] leading-[1.5] text-muted-foreground md:text-right">
                {client.risk_profile} ·{" "}
                {client.service_models.join(", ").toLowerCase()}
                <br />
                {money(client.aum_usd)} · client since{" "}
                {year(client.client_since)}
                {client.age ? <> · age {client.age}</> : null}
              </div>
            </div>

            {/* The unanswered question, flagged once. Text beside the
                colour, never colour alone. */}
            {question?.unanswered_question && (
              <div className="mt-3.5 inline-block rounded-[3px] bg-crest/[0.08] px-3.5 py-1.5 text-[13px] text-crest">
                He asked you a question on{" "}
                {shortDate(question.unanswered_question.asked_on)}. It has no
                answer yet.
              </div>
            )}

            {/* 2 — what he asked for, quoted */}
            <p className="font-read mt-6 max-w-[56ch] text-[17px] leading-[1.6] text-prose md:text-[19px]">
              {client.source_of_wealth.replace(/^Entrepreneur - /, "His money came from ")}
              . What he asked us for, in {year(client.client_since)}, was{" "}
              <b className="font-medium text-ink shadow-[inset_0_-8px_0_rgba(199,147,85,.22)]">
                {client.objectives}
              </b>
              .
            </p>

            {/* The four-into-one figure */}
            {exposure && (
              <ExposureFigure
                finding={exposure}
                duplicate={duplicate}
                snapshotDate={shortDate(snapshot)}
              />
            )}
          </Band>

          {/* How it got here */}
          {exposure?.trajectory && exposure.trajectory.length > 1 && (
            <Band>
              <Trajectory finding={exposure} />
            </Band>
          )}

          {/* What the portfolio did, and why. Building Block 1. Spec 008. */}
          {explained && (
            <Band>
              <ExplanationPanel finding={explained} />
            </Band>
          )}

          {/* 3 — the brief itself */}
          {client.brief && client.brief.paragraphs.length > 0 && (
            <Band>
              <div className="prose-brief">
                {client.brief.paragraphs.map((paragraph, index) => (
                  <p key={index}>{paragraph}</p>
                ))}
              </div>
            </Band>
          )}

          {/* 4 — THE MANDATE PANEL. This carries the argument. */}
          <Band>
            <MandatePanel client={client} />
          </Band>

          {/* 5 — THE SCENARIO PANEL */}
          {repricing && (
            <Band>
              <ScenarioPanel finding={repricing} question={question} />
            </Band>
          )}

          {/* What he said, against what he holds */}
          {said && (
            <Band>
              <h3 className="font-read text-[20px] font-normal">
                What he said, against what he holds
              </h3>
              <p className="font-read mt-3 max-w-[62ch] text-[16px] leading-[1.65] text-prose md:text-[17.5px]">
                {said.detail}
              </p>
              <Decisions findingKey={`${client.client_id}-D1`} />
            </Band>
          )}

          {/* Liquidity, where it constrains something */}
          {runway.length > 0 && (
            <Band>
              <h3 className="font-read text-[20px] font-normal">
                What is already committed
              </h3>
              {runway.map((finding, index) => (
                <div key={index} className="mt-3">
                  <p className="font-read max-w-[62ch] text-[16px] leading-[1.65] text-prose md:text-[17.5px]">
                    {finding.detail}
                  </p>
                </div>
              ))}
              <Decisions findingKey={`${client.client_id}-D4`} />
            </Band>
          )}

          {/* The profile, against the client's own plans. Spec 008. */}
          {profile && (
            <Band>
              <h3 className="font-read text-[20px] font-normal">
                What the profile says, against what he has planned
              </h3>
              <p className="font-read mt-3 max-w-[62ch] text-[16px] leading-[1.65] text-prose md:text-[17.5px]">
                {profile.detail}
              </p>
              <Decisions findingKey={`${client.client_id}-D10`} />
            </Band>
          )}

          {/* The tax position at domicile. Reports; never optimises. Spec 008. */}
          {tax && (
            <Band>
              <h3 className="font-read text-[20px] font-normal">
                The tax position, at domicile
              </h3>
              <p className="font-read mt-3 max-w-[62ch] text-[16px] leading-[1.65] text-prose md:text-[17.5px]">
                {tax.detail}
              </p>
              <p className="mt-3 max-w-[64ch] text-[13px] leading-[1.6] text-muted-foreground">
                {tax.unsure_about}
              </p>
              <Decisions findingKey={`${client.client_id}-D9`} />
            </Band>
          )}

          {/* The loan against the portfolio, over time. Spec 008. */}
          {runway.some((f) => f.facility_trajectory) && (
            <Band>
              <CollateralTrajectory
                finding={runway.find((f) => f.facility_trajectory)!}
              />
            </Band>
          )}

          {/* 6 and 7 — the opening line, and she decides */}
          {client.brief?.opening_line && (
            <div className="bg-navy px-6 py-9 text-white md:px-11 md:py-10">
              <div className="mb-3.5 text-[13px] opacity-70">
                Worth opening with
              </div>
              <blockquote className="opening-line">
                {client.brief.opening_line}
              </blockquote>
              <p className="mt-4.5 max-w-[56ch] text-[13.5px] leading-[1.6] opacity-[0.72]">
                Drafted from the findings above. Every figure in it was
                computed before the sentence was written.
              </p>
              <Decisions findingKey={`${client.client_id}-brief`} onDark />
            </div>
          )}

          {/* A client with nothing to say about */}
          {client.findings.length === 0 && (
            <Band>
              <p className="font-read max-w-[62ch] text-[17.5px] leading-[1.65]">
                Nothing worth a conversation today. Every band was checked and
                every one is respected.
              </p>
            </Band>
          )}
        </Sheet>

        {/* Where this client's figures came from, when there is no brief */}
        {client.depth !== "full" && (
          <p className="mt-4 max-w-[64ch] text-[13px] leading-[1.6] text-muted-foreground">
            This client was run through the mandate and look-through checks
            only. The notes, liquidity and scenario detectors ran for the
            three clients on today&rsquo;s list.
          </p>
        )}

        <p className="mt-6">
          <Link
            href="/"
            className="text-[13.5px] text-muted-foreground hover:text-ink"
          >
            Back to the call list
          </Link>
        </p>
      </div>

      {/* 8 — evidence, visible without interaction on desktop */}
      <EvidenceColumn findings={client.findings} />
    </div>
  );
}
