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

// Deterministic 16-digit demo NID derived from name+dob.
// Real Rwandan NIDs encode sex/year — for the demo we just need 16 digits.
function deriveNid(first: string, last: string, dob: string, sex: Sex | ""): string {
  const seed = `${slugify(first)}-${slugify(last)}-${dob}`;
  // FNV-1a-ish digit accumulator; safe for ES2017 target.
  let acc = 0;
  for (const ch of seed) acc = (acc * 31 + ch.charCodeAt(0)) >>> 0;
  const sexDigit = sex === "F" ? "2" : "1";
  const yearTwo = dob.slice(2, 4) || "00";
  // expand hash to a 13-digit tail by chaining modulo + length
  const baseTail = (acc.toString() + (acc * 1009).toString() + seed.length.toString()).replace(
    /\D/g,
    "",
  );
  const tail = baseTail.padStart(13, "0").slice(0, 13);
  return `${sexDigit}${yearTwo}${tail}`.slice(0, 16);
}

function formatRwf(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

type Field = {
  label: string;
  hint?: string;
  required?: boolean;
};

function Label({ label, hint, required }: Field) {
  return (
    <span className="flex items-baseline justify-between">
      <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
        {label}
        {required ? <span className="ml-0.5 text-red-500">*</span> : null}
      </span>
      {hint ? (
        <span className="text-[10px] text-zinc-400 dark:text-zinc-500">{hint}</span>
      ) : null}
    </span>
  );
}

const inputCls =
  "mt-1 w-full rounded-md border border-zinc-200 bg-white px-2 py-1.5 text-sm placeholder-zinc-400 focus:border-zinc-400 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:placeholder-zinc-500";

const selectCls = inputCls;

const COVERAGE_PRESETS = [2_000_000, 5_000_000, 10_000_000, 20_000_000];

export function ApplicantForm({ districts }: { districts: District[] }) {
  const router = useRouter();
  const districtsByName = useMemo(
    () => new Map(districts.map((d) => [d.name, d.province])),
    [districts],
  );

  // -- About you --------------------------------------------------------
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dob, setDob] = useState("");
  const [sex, setSex] = useState<Sex | "">("");
  const [email, setEmail] = useState("");

  // -- Location & work --------------------------------------------------
  const [district, setDistrict] = useState("");
  const [occTitle, setOccTitle] = useState("");
  const [occClass, setOccClass] = useState<OccupationClass>("I");

  // -- Health -----------------------------------------------------------
  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [tobacco, setTobacco] = useState<Tobacco>("none");
  const [history, setHistory] = useState("");

  // -- Coverage ---------------------------------------------------------
  const [sumInsured, setSumInsured] = useState(5_000_000);

  // -- Documents --------------------------------------------------------
  const [files, setFiles] = useState<File[]>([]);

  // -- Underwriter details (collapsed, pre-filled) ----------------------
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [nidOverride, setNidOverride] = useState("");
  const [phone, setPhone] = useState("");
  const [ubudehe, setUbudehe] = useState<UbudeheCategory>(3);
  const [cbhi, setCbhi] = useState<CbhiStatus>("enrolled");
  const [sbp, setSbp] = useState("");
  const [dbp, setDbp] = useState("");
  const [alcohol, setAlcohol] = useState(0);
  const [exercise, setExercise] = useState(3);

  // -- Derived ----------------------------------------------------------
  const province = district ? (districtsByName.get(district) ?? "") : "";
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
    <form onSubmit={onSubmit} className="space-y-6" autoComplete="off">
      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      ) : null}

      <Section title="About you">
        <div className="grid grid-cols-2 gap-3">
          <label>
            <Label label="First name" required />
            <input
              className={inputCls}
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
              autoComplete="given-name"
            />
          </label>
          <label>
            <Label label="Last name" required />
            <input
              className={inputCls}
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
              autoComplete="family-name"
            />
          </label>
          <label>
            <Label label="Date of birth" required />
            <input
              type="date"
              className={inputCls}
              value={dob}
              onChange={(e) => setDob(e.target.value)}
              max={TODAY}
              required
            />
          </label>
          <label>
            <Label label="Sex" required />
            <select
              className={selectCls}
              value={sex}
              onChange={(e) => setSex(e.target.value as Sex | "")}
              required
            >
              <option value="">—</option>
              <option value="M">Male</option>
              <option value="F">Female</option>
            </select>
          </label>
          <label className="col-span-2">
            <Label label="Email" hint="we'll send the decision here" required />
            <input
              type="email"
              className={inputCls}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </label>
        </div>
      </Section>

      <Section title="Location and work">
        <div className="grid grid-cols-2 gap-3">
          <label>
            <Label label="District" required />
            <select
              className={selectCls}
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
            {province ? (
              <span className="mt-1 block text-[10px] text-zinc-500 dark:text-zinc-400">
                {province} province
              </span>
            ) : null}
          </label>
          <label>
            <Label label="Occupation" required />
            <input
              className={inputCls}
              value={occTitle}
              onChange={(e) => setOccTitle(e.target.value)}
              placeholder="e.g. Teacher"
              required
            />
          </label>
          <label className="col-span-2">
            <Label label="Job risk level" />
            <select
              className={selectCls}
              value={occClass}
              onChange={(e) => setOccClass(e.target.value as OccupationClass)}
            >
              <option value="I">Office / professional / teacher</option>
              <option value="II">Farmer / nurse / construction</option>
              <option value="III">Mining / motorcycle taxi / pesticides</option>
            </select>
          </label>
        </div>
      </Section>

      <Section title="Your health">
        <div className="grid grid-cols-2 gap-3">
          <label>
            <Label label="Height (cm)" required />
            <input
              type="number"
              className={inputCls}
              value={heightCm}
              onChange={(e) => setHeightCm(e.target.value)}
              min={50}
              max={250}
              step="1"
              placeholder="170"
              required
            />
          </label>
          <label>
            <Label label="Weight (kg)" required />
            <input
              type="number"
              className={inputCls}
              value={weightKg}
              onChange={(e) => setWeightKg(e.target.value)}
              min={20}
              max={300}
              step="0.5"
              placeholder="70"
              required
            />
          </label>
          <label className="col-span-2">
            <Label label="Smoking" />
            <select
              className={selectCls}
              value={tobacco}
              onChange={(e) => setTobacco(e.target.value as Tobacco)}
            >
              <option value="none">I don&apos;t smoke</option>
              <option value="occasional">Occasionally</option>
              <option value="daily">Daily</option>
            </select>
          </label>
          <label className="col-span-2">
            <Label
              label="Existing conditions"
              hint="optional — one per line"
            />
            <textarea
              className={`${inputCls} font-mono text-xs`}
              rows={3}
              value={history}
              onChange={(e) => setHistory(e.target.value)}
              placeholder={"e.g.\nhypertension\ntype 2 diabetes"}
            />
          </label>
        </div>
      </Section>

      <Section title="Coverage">
        <Label label="Coverage amount (RWF)" required />
        <div className="mt-1 flex flex-wrap gap-2">
          {COVERAGE_PRESETS.map((amt) => (
            <button
              key={amt}
              type="button"
              onClick={() => setSumInsured(amt)}
              className={`rounded-md border px-3 py-1 text-xs font-medium ${
                sumInsured === amt
                  ? "border-zinc-900 bg-zinc-900 text-white dark:border-white dark:bg-white dark:text-zinc-900"
                  : "border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
              }`}
            >
              {formatRwf(amt)}
            </button>
          ))}
        </div>
        <div className="mt-2">
          <input
            type="number"
            className={inputCls}
            value={sumInsured}
            onChange={(e) => setSumInsured(Number(e.target.value) || 0)}
            min={500_000}
            max={500_000_000}
            step={500_000}
            required
          />
          <span className="mt-1 block text-[10px] text-zinc-500 dark:text-zinc-400">
            {formatRwf(sumInsured)} RWF
          </span>
        </div>
      </Section>

      <Section title="Medical documents (optional)">
        <Label label="PDFs" hint="lab results, doctor's notes, etc." />
        <input
          type="file"
          multiple
          accept="application/pdf"
          className={`${inputCls} file:mr-3 file:rounded file:border-0 file:bg-zinc-100 file:px-2 file:py-1 file:text-xs dark:file:bg-zinc-800`}
          onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
        />
        {files.length > 0 ? (
          <ul className="mt-2 space-y-1 text-xs text-zinc-500 dark:text-zinc-400">
            {files.map((f) => (
              <li key={f.name}>
                {f.name} · {(f.size / 1024).toFixed(1)} KB
              </li>
            ))}
          </ul>
        ) : null}
      </Section>

      <Advanced
        open={showAdvanced}
        onToggle={() => setShowAdvanced((v) => !v)}
        derivedNid={derivedNid}
        nid={nid}
        nidOverride={nidOverride}
        setNidOverride={setNidOverride}
        phone={phone}
        setPhone={setPhone}
        ubudehe={ubudehe}
        setUbudehe={setUbudehe}
        cbhi={cbhi}
        setCbhi={setCbhi}
        sbp={sbp}
        setSbp={setSbp}
        dbp={dbp}
        setDbp={setDbp}
        alcohol={alcohol}
        setAlcohol={setAlcohol}
        exercise={exercise}
        setExercise={setExercise}
      />

      <div className="flex items-center gap-3 border-t border-zinc-200 pt-4 dark:border-zinc-800">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
        >
          {submitting ? "submitting…" : "run underwriting"}
        </button>
        <span className="text-xs text-zinc-500 dark:text-zinc-400">
          The pipeline will start in the background and stream results live.
        </span>
      </div>
    </form>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        {title}
      </h2>
      <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
        {children}
      </div>
    </section>
  );
}

type AdvancedProps = {
  open: boolean;
  onToggle: () => void;
  derivedNid: string;
  nid: string;
  nidOverride: string;
  setNidOverride: (v: string) => void;
  phone: string;
  setPhone: (v: string) => void;
  ubudehe: UbudeheCategory;
  setUbudehe: (v: UbudeheCategory) => void;
  cbhi: CbhiStatus;
  setCbhi: (v: CbhiStatus) => void;
  sbp: string;
  setSbp: (v: string) => void;
  dbp: string;
  setDbp: (v: string) => void;
  alcohol: number;
  setAlcohol: (v: number) => void;
  exercise: number;
  setExercise: (v: number) => void;
};

function Advanced(props: AdvancedProps) {
  const {
    open,
    onToggle,
    derivedNid,
    nid,
    nidOverride,
    setNidOverride,
    phone,
    setPhone,
    ubudehe,
    setUbudehe,
    cbhi,
    setCbhi,
    sbp,
    setSbp,
    dbp,
    setDbp,
    alcohol,
    setAlcohol,
    exercise,
    setExercise,
  } = props;

  return (
    <section>
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-3 text-left text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-300 dark:hover:bg-zinc-900"
        aria-expanded={open}
      >
        <span>
          Underwriter details
          <span className="ml-2 text-xs font-normal text-zinc-500 dark:text-zinc-400">
            optional · pre-filled with sensible defaults
          </span>
        </span>
        <span className="text-zinc-400">{open ? "−" : "+"}</span>
      </button>
      {open ? (
        <div className="mt-2 space-y-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
          <label className="block">
            <Label
              label="National ID"
              hint={
                derivedNid && !nidOverride
                  ? "auto-generated from name + DOB"
                  : "16 digits"
              }
            />
            <input
              className={inputCls}
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
            <Label label="Phone" hint="optional" />
            <input
              type="tel"
              className={inputCls}
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+250788000000"
              autoComplete="tel"
            />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label>
              <Label label="Ubudehe category" hint="3 is typical" />
              <select
                className={selectCls}
                value={String(ubudehe)}
                onChange={(e) =>
                  setUbudehe(Number(e.target.value) as UbudeheCategory)
                }
              >
                <option value="1">1 — most vulnerable</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4 — least vulnerable</option>
              </select>
            </label>
            <label>
              <Label label="Mutuelle de Santé" />
              <select
                className={selectCls}
                value={cbhi}
                onChange={(e) => setCbhi(e.target.value as CbhiStatus)}
              >
                <option value="enrolled">Enrolled</option>
                <option value="lapsed">Lapsed</option>
                <option value="not_applicable">Not applicable</option>
              </select>
            </label>
          </div>

          <div className="grid grid-cols-4 gap-3">
            <label>
              <Label label="SBP" hint="mmHg" />
              <input
                type="number"
                className={inputCls}
                value={sbp}
                onChange={(e) => setSbp(e.target.value)}
                min={60}
                max={250}
              />
            </label>
            <label>
              <Label label="DBP" hint="mmHg" />
              <input
                type="number"
                className={inputCls}
                value={dbp}
                onChange={(e) => setDbp(e.target.value)}
                min={40}
                max={150}
              />
            </label>
            <label>
              <Label label="Alcohol drinks/wk" />
              <input
                type="number"
                className={inputCls}
                value={alcohol}
                onChange={(e) => setAlcohol(Number(e.target.value) || 0)}
                min={0}
                max={100}
              />
            </label>
            <label>
              <Label label="Exercise days/wk" />
              <input
                type="number"
                className={inputCls}
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
  );
}
