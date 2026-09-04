/**
 * Typed access to the one committed artifact.
 *
 * A static import, not a fetch. The file ships with the page, so a
 * loading state would be theatre — and the constitution's whole reason
 * for committing it was that nothing runs at demo time.
 *
 * Nothing about a client is written here. Every id, name and figure comes
 * from the file (Principle XI).
 */

import data from "@/public/findings.json";

export type Evidence = {
  file: string;
  rows: string[];
  note?: string;
};

export type Band = {
  portfolio_id: string;
  mandate_code: string;
  asset_class: string;
  actual_pct: number;
  min_pct: number;
  max_pct: number;
  target_pct: number;
  verdict: "within" | "below_min" | "above_max";
};

export type Position = {
  instrument_id: string;
  instrument_name: string;
  asset_class: string;
  w: number;
};

export type ScenarioPosition = {
  instrument_id: string;
  instrument_name: string;
  value_now_usd: number;
  value_then_usd: number;
  impact_usd: number;
  proxied_from: string | null;
};

export type Finding = {
  client_id: string;
  kind: "D1" | "D2" | "D3" | "D4" | "D5" | "D6";
  rule?: string;
  check?: string;
  severity: number;
  confidence: string;
  headline: string;
  detail: string;
  evidence: Evidence[];
  events: string[];
  unsure_about?: string;
  classification?: string | null;
  compliance_clean?: boolean;

  // D3
  theme?: string;
  theme_pct?: number;
  members?: Position[];
  asset_classes?: string[];
  trajectory?: { snapshot_date: string; pct: number }[];
  duplicated_instrument_ids?: string[];
  referencing_instrument_id?: string;

  // D1
  claim?: { claim: string; check: string; target: string | null; source: string; stated_on: string | null };
  supporting_claims?: { claim: string; source: string }[];
  target?: string | null;
  look_through_pct?: number;
  direct_pct?: number | null;

  // D2
  asset_class?: string;
  actual_pct?: number;
  min_pct?: number;
  max_pct?: number;
  verdict?: string;
  bands_checked?: Band[];

  // D4
  obligation?: {
    id: string;
    description: string;
    currency: string;
    amount: number;
    amount_usd: number | null;
    due_from: string;
    due_to: string;
    certainty: string;
  };
  need_pct?: number;
  cover_ratio?: number;
  near_cash_cover_ratio?: number;
  funding_blocked_by_facility?: boolean;
  facility?: {
    facility_id: string;
    currency: string;
    drawn: number;
    ltv_pct: number;
    margin_call_ltv_pct: number;
    history?: {
      snapshot_date: string;
      ltv_pct: number;
      drawn: number;
      headroom: number;
      collateral_market_value: number;
    }[];
  } | null;
  facility_after_sale?: { ltv_pct_after: number | null; breaches_margin_call: boolean } | null;
  facility_trajectory?: {
    ltv_from: number;
    ltv_to: number;
    ltv_change_pp: number;
    direction: string;
    headroom_from: number | null;
    headroom_to: number | null;
    headroom_lost: number | null;
    pp_to_margin_call: number;
    balance_changes: { snapshot_date: string; from: number; to: number; delta: number; kind: string }[];
    collateral_driven_rises: { snapshot_date: string; ltv_rise_pp: number; collateral_fall: number }[];
  } | null;
  liquidity?: { liquid_pct: number; near_cash_pct: number; by_tier: Record<string, number> };

  // D5
  unanswered_question?: { note_id: string; asked_on: string; question: string };

  // D6
  scenario?: {
    series_id: string;
    series_name: string | null;
    value_now: number | null;
    value_then: number | null;
    unit: string | null;
    date_now: string;
    date_then: string;
  };
  positions?: ScenarioPosition[];
  total_impact_usd?: number;
  total_impact_pct?: number;
  second_order?: {
    source_of_wealth: string;
    notes: { note_id: string; note_date: string; quote: string }[];
  } | null;
};

export type Note = {
  note_id: string;
  client_id: string;
  note_date: string;
  rm_name: string;
  channel: string;
  note: string;
};

export type ClientRecord = {
  client_id: string;
  name: string;
  age: number | null;
  life_stage: string;
  risk_profile: string;
  source_of_wealth: string;
  objectives: string;
  tax_domicile: string;
  base_currency: string;
  client_since: string;
  aum_usd: number;
  mandate_codes: string[];
  service_models: string[];
  rm_name: string;
  depth: "full" | "mandate_and_lookthrough";
  brief: { paragraphs: string[]; opening_line: string; provenance: string } | null;
  findings: Finding[];
  notes: Note[];
  mandate_panel: {
    bands: Band[];
    clean: boolean;
    breached_bands: Band[];
    breached_positions: {
      instrument_id: string;
      instrument_name: string;
      actual_pct: number;
      max_single_position_pct: number;
    }[];
    over_limit_but_exempt: {
      instrument_id: string;
      instrument_name: string;
      actual_pct: number;
      max_single_position_pct: number;
    }[];
    largest_position: {
      instrument_id: string;
      instrument_name: string;
      actual_pct: number;
      limit_pct: number | null;
    } | null;
    custody: {
      portfolio_id: string;
      portfolio_name: string;
      value_usd: number;
      status: string;
    }[];
  };
};

export type CallListEntry = {
  rank: number;
  client_id: string;
  name: string;
  aum_usd: number;
  why: string;
  finding_count: number;
  has_brief: boolean;
  compliance_clean: boolean | null;
};

export type Imperfection = {
  kind: string;
  file: string;
  client_id: string;
  portfolio_id: string;
  instrument_id: string;
  snapshot_date: string;
  field: string;
  detail: string;
};

export type MethodLimit = {
  client_id: string;
  kind: string;
  headline: string;
  unsure_about: string;
};

export type FindingsFile = {
  meta: {
    snapshot_date: string;
    snapshots: string[];
    scenario: { series_id: string; date_now: string; date_then: string };
    rm_name: string;
    client_count: number;
    deep_clients: string[];
    ranking_corrections: string[];
  };
  call_list: CallListEntry[];
  clients: Record<string, ClientRecord>;
  uncertainty: {
    data_imperfections: Imperfection[];
    method_limits: MethodLimit[];
  };
};

export const findings = data as unknown as FindingsFile;

export function getClient(id: string): ClientRecord | undefined {
  return findings.clients[id];
}

export function clientIds(): string[] {
  return Object.keys(findings.clients);
}

/** Findings of one kind, for one client. */
export function byKind(client: ClientRecord, kind: Finding["kind"]): Finding[] {
  return client.findings.filter((f) => f.kind === kind);
}

/**
 * The look-through concentration finding — the hero of the whole thing.
 * The sector rule is the one that reaches the recorded figure; see spec 001.
 */
export function lookThrough(client: ClientRecord): Finding | undefined {
  return byKind(client, "D3").find((f) => f.rule === "sector");
}

export function duplicateUnderlying(client: ClientRecord): Finding | undefined {
  return byKind(client, "D3").find((f) => f.rule === "duplicate_underlying");
}

export function scenario(client: ClientRecord): Finding | undefined {
  return byKind(client, "D6")[0];
}

export function openQuestion(client: ClientRecord): Finding | undefined {
  return byKind(client, "D5")[0];
}

export function saidVsHeld(client: ClientRecord): Finding | undefined {
  return byKind(client, "D1")[0];
}

/**
 * Clients with nothing worth a conversation today.
 *
 * Derived, never written into the copy — block 9 wants the count stated,
 * and a hardcoded "sixteen" would drift the moment the data changed.
 * A mandate check that came back clean is not a finding; it is the
 * absence of one.
 */
export function nothingTodayCount(): number {
  return findings.call_list.filter((entry) => {
    const client = findings.clients[entry.client_id];
    if (!client) return true;
    return client.findings.every(
      (f) => f.kind === "D2" && f.verdict === "within"
    );
  }).length;
}

export function hasNothingToday(client: ClientRecord): boolean {
  return client.findings.every(
    (f) => f.kind === "D2" && f.verdict === "within"
  );
}
