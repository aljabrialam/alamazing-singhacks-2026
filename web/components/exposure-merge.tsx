"use client";

/**
 * **The one orchestrated moment.** Spec 009, FR-014 to FR-018.
 *
 * The four blocks merge into one bar when the button is pressed — at the
 * exact point in the pitch where the presenter says "look through the
 * note". That is the whole product in two seconds, and it happens *while
 * they are talking*.
 *
 * From the design notes, verbatim on the mechanism:
 *
 *   "one CSS class toggle, `.merged` on the container. In React that is
 *    `useState(false)` and a `className` ternary. No animation library,
 *    nothing to debug at 15:00."
 *
 * So: one boolean. No effect, no ref, no timer, no library. The button
 * resets on the second press so the moment can be rehearsed repeatedly
 * and re-run if a take is fumbled.
 *
 * **Every toggled property is an inline style rather than a swapped
 * Tailwind class, and that is not a stylistic preference.** Conflicting
 * utilities resolve by declaration order in the compiled stylesheet, not
 * by the order they appear in JSX. In this build `opacity-80` compiles
 * *after* `opacity-0`, so a `merged ? "opacity-0" : ""` ternary beside a
 * base `opacity-80` silently never fades — and the same for
 * `opacity-100`/`opacity-0` on the hint, `gap-0`/`gap-2.5`, and
 * `rounded-none`/`rounded-[2px]`. All four would have failed on stage
 * while looking correct in the source. Inline styles have no such
 * ordering problem.
 *
 * **This component holds no `Finding` and does no arithmetic.** Every
 * figure arrives as an already-formatted string from the server component
 * above it, so the block percentages and the combined figure cannot
 * disagree — they were computed once, from one record. Principle V holds
 * structurally here rather than by discipline: there is nothing in this
 * file that could count even if someone tried.
 *
 * Text colour is carried per block rather than set once, because the tint
 * ramp needs dark text on its lighter values to clear AA — the mockup's
 * white-on-everything is 2.25:1 on `--e1`. research.md R6.
 */
import { useState } from "react";

export type MergeBlock = {
  id: string;
  assetClass: string;
  name: string;
  pctLabel: string;
  bg: string;
  fg: string;
};

const EASE = "var(--ease)";

export function ExposureMerge({
  blocks,
  combinedLabel,
  sentence,
  mergedBg,
  mergedFg,
  barBg,
  barFg,
  buttonLabel,
  resetLabel,
  hint,
}: {
  blocks: MergeBlock[];
  combinedLabel: string;
  sentence: string;
  mergedBg: string;
  mergedFg: string;
  barBg: string;
  barFg: string;
  buttonLabel: string;
  resetLabel: string;
  hint: string;
}) {
  const [merged, setMerged] = useState(false);

  return (
    <div>
      <div
        className="grid grid-cols-2 md:grid-cols-4"
        style={{
          gap: merged ? 0 : 10,
          transition: `gap .7s ${EASE}`,
        }}
      >
        {blocks.map((block) => (
          <div
            key={block.id}
            className="px-4 pt-[17px] pb-[19px]"
            style={{
              background: merged ? mergedBg : block.bg,
              color: merged ? mergedFg : block.fg,
              borderRadius: merged ? 0 : 2,
              transition: `background-color .7s ${EASE}, color .7s ${EASE}, border-radius .7s ${EASE}`,
            }}
          >
            {/* The labels are what make four positions look like four
                different things. They fade, and the sameness is left. */}
            <div
              className="text-[11.5px]"
              style={{
                opacity: merged ? 0 : 0.8,
                transition: "opacity .35s",
              }}
            >
              {block.assetClass}
            </div>
            <div
              className="mt-[5px] min-h-[36px] text-[13.5px] leading-[1.35]"
              style={{
                opacity: merged ? 0 : 1,
                transition: "opacity .35s",
              }}
            >
              {block.name}
            </div>
            <div className="font-read mt-2 text-[26px] tabular">
              {block.pctLabel}
            </div>
          </div>
        ))}
      </div>

      {/* The combined bar. Height rather than display, so it slides.
          aria-hidden while collapsed — a screen reader should not be told
          about a figure that is not on screen yet. */}
      <div
        className="mt-3 overflow-hidden"
        style={{
          height: merged ? 72 : 0,
          transition: `height .55s ${EASE}`,
          transitionDelay: merged ? "250ms" : "0ms",
        }}
        aria-hidden={!merged}
      >
        {/* No `flex-wrap` here, and the figure is `shrink-0`.
            With wrapping enabled the sentence took the full width and
            pushed the combined figure onto a second line, which the
            72px `overflow-hidden` above then clipped — so the merge
            revealed everything except the one number it exists to
            reveal. Caught by extracting a frame from the demo capture
            at the merged beat and looking at it. */}
        <div
          className="flex h-[72px] items-center justify-between gap-5 px-5 md:px-6"
          style={{ background: barBg, color: barFg, borderRadius: 2 }}
        >
          <div className="font-read line-clamp-2 min-w-0 text-[14px] leading-[1.3] md:text-[18px]">
            {sentence}
          </div>
          <div className="font-read shrink-0 text-[30px] leading-none tabular md:text-[36px]">
            {combinedLabel}
          </div>
        </div>
      </div>

      <div className="mt-[22px] flex flex-wrap items-center gap-4">
        <button
          type="button"
          onClick={() => setMerged((on) => !on)}
          aria-pressed={merged}
          className="rounded-[2px] border border-navy bg-navy px-[22px] py-3 text-[14.5px] text-white"
        >
          {merged ? resetLabel : buttonLabel}
        </button>
        <span
          className="font-read max-w-[52ch] text-[16px] italic text-muted-foreground"
          style={{
            opacity: merged ? 1 : 0,
            transition: "opacity .5s",
            transitionDelay: merged ? "500ms" : "0ms",
          }}
          aria-hidden={!merged}
        >
          {hint}
        </span>
      </div>
    </div>
  );
}
