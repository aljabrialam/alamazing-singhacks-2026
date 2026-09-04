/**
 * The brand frame. Spec 009.
 *
 * A 3px red rule across the top of the page, and a wordmark bar carrying
 * "Julius Bär" beside the product name the way an internal bank tool
 * would. Per design/mockup-jb.html, which design-notes.md marks Default.
 *
 * **The wordmark is set text, and that is a decision rather than a
 * shortcut.** From the design notes, verbatim:
 *
 *   "If a real brand asset surfaces before Saturday, swap the wordmark —
 *    do not invent a logo. A text wordmark is honest; a fabricated mark
 *    is not."
 *
 * It is the same principle as never inventing a figure, applied to a brand
 * asset. Colours are read from their challenge deck, not a brand guide.
 */
import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { findings } from "@/lib/findings";
import { longDate } from "@/lib/format";

export const metadata: Metadata = {
  title: "Wealth Intelligence — Julius Bär",
  description:
    "Which client to call first, what is wrong, and how to open the conversation.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const { rm_name, snapshot_date } = findings.meta;

  return (
    <html lang="en">
      <head>
        {/* The band markers start hidden so they can draw in once on
            scroll. Without JavaScript they would never appear — and the
            mandate panel is the element carrying the entire argument, so
            rendering it with no markers is not an acceptable degradation.
            research.md R4 records why this beat arming the hidden state
            from JavaScript (which flashes) and @media (scripting: enabled)
            (too new to risk on a deadline). */}
        <noscript>
          <style>{`.pin{transform:scaleY(1)!important}`}</style>
        </noscript>
      </head>
      <body>
        {/* their signature edge treatment — a line, never a fill */}
        <div className="h-[3px] bg-jb-red" />

        <div className="border-b border-hair bg-sheet">
          <div className="mx-auto flex max-w-[1140px] flex-wrap items-center justify-between gap-5 px-6 py-[18px]">
            <Link href="/" className="flex items-baseline gap-3.5">
              <span className="font-read text-[23px] tracking-[0.01em] text-navy">
                Julius Bär
              </span>
              <span className="h-5 w-px bg-hair" aria-hidden />
              <span className="text-[14px] tracking-[0.02em] text-muted-foreground">
                Wealth Intelligence
              </span>
            </Link>
            {/* The snapshot date, never today's. The brief is *as at* the
                snapshot, and saying so is what makes the figures
                defensible. spec 007 research.md R2. */}
            <div className="text-[13.5px] text-muted-foreground">
              {rm_name} · Asia desk, Singapore and Hong Kong ·{" "}
              {longDate(snapshot_date)}
            </div>
          </div>
        </div>

        <div className="mx-auto max-w-[1140px] px-6 pt-7 pb-28">
          {children}
          <nav className="mt-14 flex gap-5 border-t border-hair pt-6 text-[13.5px] text-muted-foreground">
            <Link href="/" className="hover:text-ink">
              Call list
            </Link>
            <Link href="/uncertain" className="hover:text-ink">
              What we are not sure about
            </Link>
          </nav>
        </div>
      </body>
    </html>
  );
}
