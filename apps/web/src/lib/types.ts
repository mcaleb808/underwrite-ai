// Mirrors apps/api/src/schemas/*.py - keep in sync when those change.

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

// -- ApplicantProfile (mirrors apps/api/src/schemas/applicant.py) -----------

export type Sex = "M" | "F";
export type UbudeheCategory = 1 | 2 | 3 | 4;
export type CbhiStatus = "enrolled" | "lapsed" | "not_applicable";
export type OccupationClass = "I" | "II" | "III";
export type Tobacco = "none" | "occasional" | "daily";

export type Demographics = {
  first_name: string;
  last_name: string;
  dob: string; // ISO date YYYY-MM-DD
  sex: Sex;
  email: string;
  phone_e164?: string | null;
  nid: string; // exactly 16 digits
  district: string;
  province: string;
  ubudehe_category: UbudeheCategory;
  cbhi_status: CbhiStatus;
};

export type Occupation = {
  title: string;
  class: OccupationClass; // python alias of class_
};

export type Lifestyle = {
  tobacco: Tobacco;
  alcohol_units_per_week: number;
  exercise_days_per_week: number;
};

export type Vitals = {
  height_cm: number;
  weight_kg: number;
  sbp?: number | null;
  dbp?: number | null;
};

export type ApplicantProfile = {
  applicant_id: string;
  demographics: Demographics;
  occupation: Occupation;
  lifestyle: Lifestyle;
  vitals: Vitals;
  declared_history: string[];
  sum_insured_rwf: number;
  medical_docs: string[];
};

export type District = {
  name: string;
  province: string;
};
