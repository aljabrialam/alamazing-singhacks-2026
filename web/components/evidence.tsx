/**
 * Evidence. **Always visible on desktop** — hiding it undercuts the whole
 * trust story, which is why the design notes make it a fixed column
 * rather than a drawer (Principle VI: the evidence panel MUST be visible
 * without interaction on desktop).
 *
 * Below 920px it becomes a bottom sheet, because a fixed column on a
 * phone is unreadable.
 *
 * **The only place monospace appears.** File names and row identifiers are
 * data; everything Priscilla reads is set in the serif.
 */
import type { Finding } from "@/lib/findings";

function EvidenceCard({ finding }: { finding: Finding }) {
  return (
    <div className="rounded-[4px] border border-hair px-4 py-3.5">
      <div className="font-read mb-2 text-[14px] leading-[1.4]">
        {finding.headline}
      </div>
      {finding.evidence.map((entry, index) => (
        <div key={`${entry.file}-${index}`} className="mt-2.5">
          <div className="font-num text-[11px] text-muted-foreground">
            {entry.file}
          </div>
          <div className="font-num mt-1 text-[11.5px] leading-[1.5] text-ink">
            {entry.rows.join("  ")}
          </div>
          {entry.note && (
            <div className="mt-1.5 text-[12px] leading-[1.5] text-muted-foreground">
              {entry.note}
            </div>
          )}
        </div>
      ))}
      {finding.events.length > 0 && (
        <div className="font-num mt-2.5 text-[11px] text-muted-foreground">
          event_log.csv {finding.events.join("  ")}
        </div>
      )}
    </div>
  );
}

export function EvidenceList({ findings }: { findings: Finding[] }) {
  const withEvidence = findings.filter((f) => f.evidence?.length);
  if (withEvidence.length === 0) return null;

  return (
    <div className="space-y-3">
      <div>
        <h3 className="font-read text-[18px] font-normal">Evidence</h3>
        <p className="mt-0.5 text-[13px] leading-[1.5] text-muted-foreground">
          Every sentence above traces to a row in the bank&rsquo;s own files.
        </p>
      </div>
      {withEvidence.map((finding, index) => (
        <EvidenceCard key={`${finding.kind}-${index}`} finding={finding} />
      ))}
    </div>
  );
}

/**
 * Desktop: a sticky column beside the brief, visible on load.
 * Mobile: a details element that slides open from the bottom of the flow.
 *
 * A `details` rather than a Radix dialog, deliberately — it needs no
 * JavaScript, works with the keyboard for free, and respects
 * prefers-reduced-motion without configuration. The Sheet primitive is
 * installed and available; this is simply the smaller correct tool.
 */
export function EvidenceColumn({ findings }: { findings: Finding[] }) {
  const withEvidence = findings.filter((f) => f.evidence?.length);
  if (withEvidence.length === 0) return null;

  return (
    <>
      <aside className="hidden lg:block">
        <div className="sticky top-10">
          <div className="sheet max-h-[calc(100vh-6rem)] overflow-y-auto px-5 py-6">
            <EvidenceList findings={findings} />
          </div>
        </div>
      </aside>

      <details className="sheet mt-5 lg:hidden">
        <summary className="font-ui cursor-pointer px-6 py-4 text-[14px]">
          Evidence — {withEvidence.length}{" "}
          {withEvidence.length === 1 ? "finding" : "findings"}, every row
        </summary>
        <div className="border-t border-hair px-6 py-5">
          <EvidenceList findings={findings} />
        </div>
      </details>
    </>
  );
}
