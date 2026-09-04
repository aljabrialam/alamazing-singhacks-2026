"use client";

/**
 * Keep for the meeting / Not useful / Add a note.
 *
 * **Priscilla decides.** The system proposes; she disposes (Principle
 * IX). Rejection records a reason, because a rejection without one
 * teaches the system nothing and tells her successor nothing.
 *
 * There is no server by design (Principle XIII: no database, no auth), so
 * these persist to local storage. That is stated plainly in the README
 * rather than implied — a working action that is honestly scoped beats a
 * disabled button that looks interactive, and Strategic Impact is assessed
 * on whether she retains control. research.md R6.
 */

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

type Decision = {
  verdict: "kept" | "rejected" | null;
  reason?: string;
  note?: string;
};

const STORAGE_KEY = "divergence-decisions";

function read(): Record<string, Decision> {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "{}");
  } catch {
    // Local storage unavailable or corrupt. Not an error — the actions
    // still work for this session.
    return {};
  }
}

function write(all: Record<string, Decision>) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
  } catch {
    /* nothing to do; the decision holds for this session only */
  }
}

export function Decisions({
  findingKey,
  onDark = false,
}: {
  findingKey: string;
  onDark?: boolean;
}) {
  const [decision, setDecision] = useState<Decision>({ verdict: null });
  const [asking, setAsking] = useState<null | "reason" | "note">(null);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    setDecision(read()[findingKey] ?? { verdict: null });
  }, [findingKey]);

  function save(next: Decision) {
    setDecision(next);
    const all = read();
    all[findingKey] = next;
    write(all);
  }

  // shadcn Button, per the design notes: `default` for Keep, `outline`
  // for the rest. On the navy panel the variants are re-tinted rather
  // than replaced, so the component stays the component.
  const outlineClass = onDark
    ? "font-ui border-white/[0.28] bg-transparent text-white hover:bg-white/10 hover:text-white"
    : "font-ui border-hair bg-transparent text-ink hover:bg-secondary";
  const solidClass = onDark
    ? "font-ui border border-white bg-white font-medium text-navy hover:bg-white/90"
    : "font-ui font-medium";

  if (asking) {
    return (
      <form
        className="mt-6 max-w-[46ch]"
        onSubmit={(event) => {
          event.preventDefault();
          if (asking === "reason") {
            save({ verdict: "rejected", reason: draft.trim(), note: decision.note });
          } else {
            save({ ...decision, note: draft.trim() });
          }
          setDraft("");
          setAsking(null);
        }}
      >
        <label
          className={`mb-2 block text-[13px] ${
            onDark ? "text-white/70" : "text-muted-foreground"
          }`}
          htmlFor={`${findingKey}-input`}
        >
          {asking === "reason"
            ? "Why is this not useful?"
            : "Your note for the meeting"}
        </label>
        <textarea
          id={`${findingKey}-input`}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          rows={2}
          autoFocus
          className={`w-full rounded-[3px] px-3 py-2 text-[14px] ${
            onDark
              ? "border border-white/[0.28] bg-white/10 text-white placeholder:text-white/40"
              : "border border-hair bg-white text-ink"
          }`}
          placeholder={
            asking === "reason" ? "Already discussed in June" : "Ask about the family office timing"
          }
        />
        <div className="mt-3 flex gap-2.5">
          <Button type="submit" className={solidClass}>
            Save
          </Button>
          <Button
            type="button"
            variant="outline"
            className={outlineClass}
            onClick={() => {
              setDraft("");
              setAsking(null);
            }}
          >
            Cancel
          </Button>
        </div>
      </form>
    );
  }

  return (
    <div className="mt-6">
      <div className="flex flex-wrap gap-2.5">
        <Button
          type="button"
          variant={decision.verdict === "kept" ? "default" : "outline"}
          className={decision.verdict === "kept" ? solidClass : outlineClass}
          aria-pressed={decision.verdict === "kept"}
          onClick={() =>
            save({
              verdict: decision.verdict === "kept" ? null : "kept",
              note: decision.note,
            })
          }
        >
          {decision.verdict === "kept" ? "Kept for the meeting" : "Keep for the meeting"}
        </Button>

        <Button
          type="button"
          variant="outline"
          className={outlineClass}
          aria-pressed={decision.verdict === "rejected"}
          onClick={() => {
            setDraft(decision.reason ?? "");
            setAsking("reason");
          }}
        >
          Not useful
        </Button>

        <Button
          type="button"
          variant="outline"
          className={outlineClass}
          onClick={() => {
            setDraft(decision.note ?? "");
            setAsking("note");
          }}
        >
          {decision.note ? "Edit your note" : "Add a note"}
        </Button>
      </div>

      {decision.verdict === "rejected" && (
        <p
          className={`mt-3 max-w-[52ch] text-[13px] leading-[1.6] ${
            onDark ? "text-white/70" : "text-muted-foreground"
          }`}
        >
          Marked not useful
          {decision.reason ? <>: “{decision.reason}”</> : "."}
        </p>
      )}

      {decision.note && (
        <p
          className={`mt-2 max-w-[52ch] text-[13px] leading-[1.6] ${
            onDark ? "text-white/70" : "text-muted-foreground"
          }`}
        >
          Your note: “{decision.note}”
        </p>
      )}
    </div>
  );
}
