"use client";

/**
 * The one scroll reveal. Spec 009, FR-019 and FR-020.
 *
 * The band markers draw in once, staggered, the first time the mandate
 * panel comes into view. Then they stay, and nothing on the page ever
 * moves again. From the design notes:
 *
 *   "Everything else is still. The band pins draw in once on scroll, and
 *    that is it. Motion used once is a reveal; motion used everywhere is
 *    noise."
 *
 * **This component receives no band data — only children it never looks
 * at.** It cannot misreport a figure because it never holds one. The
 * stagger comes from `--pin-delay`, set by the panel above from each
 * row's index: an ordinal, not a figure (Principle XI).
 *
 * The observer disconnects on first intersection, so scrolling away and
 * back does not re-animate.
 *
 * Note on the hidden initial state: `.pin` starts at `scaleY(0)`, so
 * without JavaScript the markers would never appear at all — on the panel
 * that carries the entire argument. `layout.tsx` carries a `<noscript>`
 * block that forces them visible. research.md R4 records why that beat
 * arming the hidden state from JavaScript, which flashes on a projector.
 */
import { useEffect, useRef, useState } from "react";

export function BandReveal({ children }: { children: React.ReactNode }) {
  const frame = useRef<HTMLDivElement>(null);
  const [seen, setSeen] = useState(false);

  useEffect(() => {
    const node = frame.current;
    if (!node) return;

    // No observer available: show the final state rather than nothing.
    if (typeof IntersectionObserver === "undefined") {
      setSeen(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setSeen(true);
          observer.disconnect();
        }
      },
      { threshold: 0.4 }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={frame} data-reveal={seen ? "seen" : "armed"}>
      {children}
    </div>
  );
}
