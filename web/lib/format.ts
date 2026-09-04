/**
 * Formatting. Figures are set in the serif alongside the prose, so they
 * are formatted to read as part of a sentence rather than as cells in a
 * table (design notes: "a percentage in the middle of a sentence is part
 * of the sentence, not a data point").
 */

/** USD 32.2m — how a banker says it aloud. */
export function money(usd: number): string {
  const abs = Math.abs(usd);
  if (abs >= 1_000_000) {
    return `USD ${(usd / 1_000_000).toFixed(1)}m`;
  }
  if (abs >= 1_000) {
    return `USD ${Math.round(usd / 1_000)}k`;
  }
  return `USD ${Math.round(usd)}`;
}

/** Full precision, grouped. For the evidence panel. */
export function exact(value: number): string {
  return value.toLocaleString("en-GB", { maximumFractionDigits: 0 });
}

export function pct(value: number, places = 2): string {
  return `${value.toFixed(places)}%`;
}

/** −2.51m. Sign always shown, because the direction is the point. */
export function signedMillions(usd: number): string {
  const sign = usd < 0 ? "−" : "+";
  return `${sign}${Math.abs(usd / 1_000_000).toFixed(2)}m`;
}

/**
 * Wednesday 26 August 2026.
 *
 * Always the snapshot date from the file, never today's — the brief is
 * *as at* the snapshot, and a page saying "today" above August figures is
 * a small dishonesty. See specs/007-workbench/research.md R2.
 */
export function longDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
}

/** 26 August 2026 — no weekday, for inline use. */
export function shortDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
}

/** 2014, from an ISO date. */
export function year(iso: string): string {
  return iso.slice(0, 4);
}
