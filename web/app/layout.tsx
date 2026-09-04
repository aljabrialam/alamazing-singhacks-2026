import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { findings } from "@/lib/findings";
import { longDate } from "@/lib/format";

export const metadata: Metadata = {
  title: "Divergence Engine",
  description:
    "Which client to call first, what is wrong, and how to open the conversation.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const { rm_name, snapshot_date } = findings.meta;

  return (
    <html lang="en">
      <body>
        <div className="mx-auto max-w-[1080px] px-6 pt-10 pb-28 md:px-6">
          <header className="mb-9">
            <Link href="/" className="inline-block">
              <h1 className="font-read text-[25px] font-normal">
                Divergence Engine
              </h1>
            </Link>
            {/* The snapshot date, never today's. The brief is *as at* the
                snapshot, and saying so is what makes the figures
                defensible. research.md R2. */}
            <p className="mt-1 text-[13px] text-muted-foreground">
              {rm_name} · Asia desk · {longDate(snapshot_date)}
            </p>
          </header>
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
