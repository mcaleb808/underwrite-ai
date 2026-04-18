// Mirrors apps/api/src/schemas/*.py — keep in sync when those change.

export type Verdict = "accept" | "accept_with_conditions" | "refer" | "decline";
export type RiskBand = "low" | "moderate" | "high" | "very_high";

export type PersonaSummary = {
  id: string;
  name: string;
  age: number;
  district: string;
  headline: string;
};

export type RiskFactor = {
  name: string;
  weight: number;
  value: number;
  contribution: number;
  source: "declared" | "parsed_medical" | "district" | "computed";
  evidence: string | null;
};

export type DecisionPayload = {
  verdict: Verdict;
  premium_loading_pct: number;
  conditions: string[];
  reasoning: string;
  citations: string[];
};

export type ApplicationStatus = {
  task_id: string;
  reference_number: string;
  status: string;
  risk_score: number | null;
  risk_band: RiskBand | null;
  risk_factors: RiskFactor[];
  decision: DecisionPayload | null;
  email_status: string | null;
  approved_by: string | null;
  created_at: string;
  updated_at: string;
};

export type CreateApplicationResponse = {
  task_id: string;
  reference_number: string;
  status: string;
  status_url: string;
};

export type ApplicationListItem = {
  task_id: string;
  reference_number: string;
  status: string;
  risk_score: number | null;
  risk_band: RiskBand | null;
  verdict: Verdict | null;
  applicant_id: string;
  created_at: string;
};

export type LiveEvent = {
  node: string;
  type: string;
  // remaining fields are node-specific
  [key: string]: unknown;
};
