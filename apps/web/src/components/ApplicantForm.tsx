"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { createApplication } from "@/lib/api";
import type {
  ApplicantProfile,
  CbhiStatus,
  District,
  OccupationClass,
  Sex,
  Tobacco,
  UbudeheCategory,
} from "@/lib/types";

const TODAY = new Date().toISOString().slice(0, 10);

function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

// Demo NID is derived from name+DOB so seed personas resolve to a stable
// 16-digit value without collecting real PII. Real Rwandan NIDs encode
// sex/year - for the demo we just need 16 digits.
function deriveNid(first: string, last: string, dob: string, sex: Sex | ""): string {
  const seed = `${slugify(first)}-${slugify(last)}-${dob}`;
  let acc = 0;
  for (const ch of seed) acc = (acc * 31 + ch.charCodeAt(0)) >>> 0;
  const sexDigit = sex === "F" ? "2" : "1";
  const yearTwo = dob.slice(2, 4) || "00";
  const baseTail = (acc.toString() + (acc * 1009).toString() + seed.length.toString()).replace(
    /\D/g,
    "",
  );
  const tail = baseTail.padStart(13, "0").slice(0, 13);
  return `${sexDigit}${yearTwo}${tail}`.slice(0, 16);
}

const fmt = (v: number) => new Intl.NumberFormat("en-US").format(v);

const COVERAGE_PRESETS = [2_000_000, 5_000_000, 10_000_000, 20_000_000];

function SectionLabel({ n, title }: { n: string; title: string }) {
  return (
    <div className="mb-5 flex items-baseline gap-3.5">
      <span className="mono text-[11px] text-muted">{n}</span>
      <h3 className="serif m-0 text-[24px] leading-[1.1]">{title}</h3>
    </div>
  );
}

function FieldLabel({
  label,
  hint,
  required,
}: {
  label: string;
  hint?: string;
  required?: boolean;
}) {
  return (
    <div className="field-label flex items-baseline justify-between">
      <span>
        {label}
        {required ? <span className="ml-0.5 text-[var(--bad)]">*</span> : null}
      </span>
      {hint ? (
        <span className="text-[10px] tracking-normal normal-case text-muted-2">
          {hint}
        </span>
      ) : null}
    </div>
  );
}

function Segmented<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: T; key?: string; main: string; sub?: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="grid border border-line" style={{ gridTemplateColumns: `repeat(${options.length}, 1fr)` }}>
      {options.map((o, i) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => onChange(o.value)}
            className={`px-3.5 py-3 text-center text-[12px] transition-colors ${
              i < options.length - 1 ? "border-r border-line" : ""
            } ${active ? "bg-ink text-paper" : "bg-paper text-ink hover:bg-paper-2"}`}
          >
            {o.key ? (
              <div className="mono text-[10px] opacity-60">{o.key}</div>
            ) : null}
            <div className={`${o.key ? "mt-0.5" : ""} font-medium`}>{o.main}</div>
            {o.sub ? (
              <div className="text-[10px] opacity-70">{o.sub}</div>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

export function ApplicantForm({ districts }: { districts: District[] }) {
  const router = useRouter();
  const districtsByName = useMemo(
    () => new Map(districts.map((d) => [d.name, d.province])),
    [districts],
  );

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dob, setDob] = useState("");
  const [sex, setSex] = useState<Sex | "">("");
  const [email, setEmail] = useState("");

  const [district, setDistrict] = useState("");
  const [occTitle, setOccTitle] = useState("");
  const [occClass, setOccClass] = useState<OccupationClass>("I");

  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [tobacco, setTobacco] = useState<Tobacco>("none");
  const [history, setHistory] = useState("");

  const [sumInsured, setSumInsured] = useState(5_000_000);

  const [files, setFiles] = useState<File[]>([]);

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [nidOverride, setNidOverride] = useState("");
  const [phone, setPhone] = useState("");
  const [ubudehe, setUbudehe] = useState<UbudeheCategory>(3);
  const [cbhi, setCbhi] = useState<CbhiStatus>("enrolled");
  const [sbp, setSbp] = useState("");
  const [dbp, setDbp] = useState("");
  const [alcohol, setAlcohol] = useState(0);
  const [exercise, setExercise] = useState(3);

  const province = district ? districtsByName.get(district) ?? "" : "";
  const derivedNid = useMemo(
    () => (firstName && lastName && dob ? deriveNid(firstName, lastName, dob, sex) : ""),
    [firstName, lastName, dob, sex],
  );
  const nid = nidOverride || derivedNid;

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function build(): ApplicantProfile {
    return {
      applicant_id: `${slugify(firstName)}-${slugify(lastName)}-${dob}`,
      demographics: {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        dob,
        sex: sex as Sex,
        email: email.trim(),
        phone_e164: phone.trim() || null,
        nid,
        district,
        province,
        ubudehe_category: ubudehe,
        cbhi_status: cbhi,
      },
      occupation: { title: occTitle.trim(), class: occClass },
      lifestyle: {
        tobacco,
        alcohol_units_per_week: alcohol,
        exercise_days_per_week: exercise,
      },
      vitals: {
        height_cm: Number(heightCm),
        weight_kg: Number(weightKg),
        sbp: sbp ? Number(sbp) : null,
        dbp: dbp ? Number(dbp) : null,
      },
      declared_history: history
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean),
      sum_insured_rwf: sumInsured,
      medical_docs: [],
    };
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!sex) {
      setError("Please pick male or female.");
      return;
    }
    if (!nid || nid.length !== 16) {
      setError("National ID must be 16 digits.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const res = await createApplication(build(), files);
      router.push(`/applications/${res.task_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} autoComplete="off" className="space-y-9">
      {error ? (
        <div
          className="rounded border px-4 py-3 text-[13px]"
          style={{
            borderColor: "color-mix(in oklch, var(--bad) 30%, var(--line))",
            background: "color-mix(in oklch, var(--bad) 8%, var(--paper))",
            color: "var(--bad)",
          }}
        >
          {error}
        </div>
      ) : null}

      <section>
        <SectionLabel n="01" title="About you" />
        <div className="grid grid-cols-1 gap-x-6 gap-y-6 sm:grid-cols-2">
          <label className="block">
            <FieldLabel label="First name" required />
            <input
              className="field"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
              autoComplete="given-name"
            />
          </label>
          <label className="block">
            <FieldLabel label="Last name" required />
            <input
              className="field"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
              autoComplete="family-name"
            />
          </label>
          <label className="block">
            <FieldLabel label="Date of birth" required />
            <input
              type="date"
              className="field"
              value={dob}
              onChange={(e) => setDob(e.target.value)}
              max={TODAY}
              required
            />
          </label>
          <div>
            <FieldLabel label="Sex" required />
            <div className="mt-2">
              <Segmented<Sex | "">
                value={sex}
                onChange={setSex}
                options={[
                  { value: "F", main: "Female" },
                  { value: "M", main: "Male" },
                ]}
              />
            </div>
          </div>
          <label className="block sm:col-span-2">
            <FieldLabel label="Email" hint="we'll send the decision here" required />
            <input
              type="email"
              className="field"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </label>
        </div>
      </section>

      <section>
        <SectionLabel n="02" title="Location & work" />
        <div className="grid grid-cols-1 gap-x-6 gap-y-6 sm:grid-cols-2">
          <label className="block">
            <FieldLabel label="District" hint={province ? `${province} province` : undefined} required />
            <select
              className="field"
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              required
            >
              <option value="">—</option>
              {districts.map((d) => (
                <option key={d.name} value={d.name}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <FieldLabel label="Occupation" required />
            <input
              className="field"
              value={occTitle}
              onChange={(e) => setOccTitle(e.target.value)}
              placeholder="e.g. Teacher"
              required
            />
          </label>
          <div className="sm:col-span-2">
            <FieldLabel label="Job risk class" />
            <div className="mt-2">
              <Segmented<OccupationClass>
                value={occClass}
                onChange={setOccClass}
                options={[
                  { value: "I",   key: "CLASS I",   main: "Office / professional" },
                  { value: "II",  key: "CLASS II",  main: "Manual / outdoor" },
                  { value: "III", key: "CLASS III", main: "Hazardous" },
                ]}
              />
            </div>
          </div>
        </div>
      </section>

      <section>
        <SectionLabel n="03" title="Health" />
        <div className="grid grid-cols-1 gap-x-6 gap-y-6 sm:grid-cols-2">
          <label className="block">
            <FieldLabel label="Height (cm)" required />
            <input
              type="number"
              className="field"
              value={heightCm}
              onChange={(e) => setHeightCm(e.target.value)}
              min={50}
              max={250}
              step="1"
              placeholder="170"
              required
            />
          </label>
          <label className="block">
            <FieldLabel label="Weight (kg)" required />
            <input
              type="number"
              className="field"
              value={weightKg}
              onChange={(e) => setWeightKg(e.target.value)}
              min={20}
              max={300}
              step="0.5"
              placeholder="70"
              required
            />
          </label>
          <label className="block sm:col-span-2">
            <FieldLabel label="Smoking" />
            <select
              className="field"
              value={tobacco}
              onChange={(e) => setTobacco(e.target.value as Tobacco)}
            >
              <option value="none">I don&apos;t smoke</option>
              <option value="occasional">Occasionally</option>
              <option value="daily">Daily</option>
            </select>
          </label>
          <label className="block sm:col-span-2">
            <FieldLabel label="Existing conditions" hint="optional · one per line" />
            <textarea
              className="field mono text-[13px]"
              rows={3}
              value={history}
              onChange={(e) => setHistory(e.target.value)}
              placeholder={"e.g.\nhypertension\ntype 2 diabetes"}
            />
          </label>
        </div>
      </section>

      <section>
        <SectionLabel n="04" title="Coverage" />
        <div className="serif tnum text-[44px] leading-none sm:text-[48px]">
          {fmt(sumInsured)}{" "}
          <span className="text-[18px] text-muted">RWF</span>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {COVERAGE_PRESETS.map((amt) => (
            <button
              key={amt}
              type="button"
              onClick={() => setSumInsured(amt)}
              className={amt === sumInsured ? "chip solid" : "chip"}
            >
              {fmt(amt / 1_000_000)}M
            </button>
          ))}
        </div>
        <label className="mt-3 block">
          <FieldLabel label="Custom amount (RWF)" hint="multiples of 500,000" />
          <input
            type="number"
            className="field"
            value={sumInsured}
            onChange={(e) => setSumInsured(Number(e.target.value) || 0)}
            min={500_000}
            max={500_000_000}
            step={500_000}
            required
          />
        </label>
      </section>

      <section>
        <SectionLabel n="05" title="Medical documents" />
        <label className="block cursor-pointer rounded border border-dashed border-line-2 px-6 py-7 text-center text-muted">
          <div className="serif text-[18px] text-ink">Drop PDFs here</div>
          <div className="mt-1 text-[12px]">optional · lab results, doctor&apos;s notes</div>
          <input
            type="file"
            multiple
            accept="application/pdf"
            className="hidden"
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
          />
        </label>
        {files.length > 0 ? (
          <ul className="mt-3 space-y-1 text-[12px] text-muted">
            {files.map((f) => (
              <li key={f.name} className="mono">
                {f.name} · {(f.size / 1024).toFixed(1)} KB
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <section>
        <button
          type="button"
          onClick={() => setShowAdvanced((v) => !v)}
          aria-expanded={showAdvanced}
          className="flex w-full items-center justify-between rounded border border-line-2 bg-paper px-4 py-3 text-left text-[13px] hover:bg-paper-2"
        >
          <span>
            + Underwriter details{" "}
            <span className="text-muted">· optional</span>
          </span>
          <span className="text-muted">{showAdvanced ? "−" : "›"}</span>
        </button>

        {showAdvanced ? (
          <div className="mt-4 space-y-6 rounded border border-line bg-paper p-5">
            <label className="block">
              <FieldLabel
                label="National ID"
                hint={derivedNid && !nidOverride ? "auto-generated from name + DOB" : "16 digits"}
              />
              <input
                className="field mono"
                value={nid}
                onChange={(e) =>
                  setNidOverride(e.target.value.replace(/\D/g, "").slice(0, 16))
                }
                pattern="\d{16}"
                minLength={16}
                maxLength={16}
                inputMode="numeric"
              />
            </label>

            <label className="block">
              <FieldLabel label="Phone" hint="optional" />
              <input
                type="tel"
                className="field"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+250788000000"
                autoComplete="tel"
              />
            </label>

            <div className="grid grid-cols-1 gap-x-6 gap-y-6 sm:grid-cols-2">
              <label className="block">
                <FieldLabel label="Ubudehe category" hint="3 is typical" />
                <select
                  className="field"
                  value={String(ubudehe)}
                  onChange={(e) =>
                    setUbudehe(Number(e.target.value) as UbudeheCategory)
                  }
                >
                  <option value="1">1 - most vulnerable</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                  <option value="4">4 - least vulnerable</option>
                </select>
              </label>
              <label className="block">
                <FieldLabel label="Mutuelle de Santé" />
                <select
                  className="field"
                  value={cbhi}
                  onChange={(e) => setCbhi(e.target.value as CbhiStatus)}
                >
                  <option value="enrolled">Enrolled</option>
                  <option value="lapsed">Lapsed</option>
                  <option value="not_applicable">Not applicable</option>
                </select>
              </label>
            </div>

            <div className="grid grid-cols-2 gap-x-6 gap-y-6 sm:grid-cols-4">
              <label className="block">
                <FieldLabel label="SBP" hint="mmHg" />
                <input
                  type="number"
                  className="field"
                  value={sbp}
                  onChange={(e) => setSbp(e.target.value)}
                  min={60}
                  max={250}
                />
              </label>
              <label className="block">
                <FieldLabel label="DBP" hint="mmHg" />
                <input
                  type="number"
                  className="field"
                  value={dbp}
                  onChange={(e) => setDbp(e.target.value)}
                  min={40}
                  max={150}
                />
              </label>
              <label className="block">
                <FieldLabel label="Alcohol drinks/wk" />
                <input
                  type="number"
                  className="field"
                  value={alcohol}
                  onChange={(e) => setAlcohol(Number(e.target.value) || 0)}
                  min={0}
                  max={100}
                />
              </label>
              <label className="block">
                <FieldLabel label="Exercise days/wk" />
                <input
                  type="number"
                  className="field"
                  value={exercise}
                  onChange={(e) => setExercise(Number(e.target.value) || 0)}
                  min={0}
                  max={7}
                />
              </label>
            </div>
          </div>
        ) : null}
      </section>

      <div className="flex flex-wrap items-center gap-4 border-t border-line pt-5">
        <button type="submit" disabled={submitting} className="btn">
          {submitting ? "Submitting…" : "Run underwriting →"}
        </button>
        <span className="text-[12px] text-muted">
          Streams live · usually under 15 seconds
        </span>
      </div>
    </form>
  );
}
