/**
 * The paper primitive.
 *
 * White sheets floating on the ground with two shadows — a tight contact
 * shadow and a wide soft one. That is what makes paper look like paper
 * rather than a card component (design notes, Layout).
 *
 * One sheet per document, never one per paragraph.
 */
export function Caption({ children }: { children: React.ReactNode }) {
  return <div className="caption mt-12 mb-3.5 first:mt-0">{children}</div>;
}

export function Sheet({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={`sheet ${className}`}>{children}</div>;
}

/** A band within a sheet, divided by a hairline rather than a boxed header. */
export function Band({
  children,
  first = false,
  className = "",
}: {
  children: React.ReactNode;
  first?: boolean;
  className?: string;
}) {
  return (
    <section
      className={`px-6 py-7 md:px-11 ${
        first ? "" : "border-t border-hair"
      } ${className}`}
    >
      {children}
    </section>
  );
}

/** Quiet label above a block. Sentence case, never all-caps. */
export function Label({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-4 text-[13.5px] text-muted-foreground">{children}</div>
  );
}
