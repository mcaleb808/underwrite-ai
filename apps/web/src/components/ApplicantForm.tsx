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

export function ApplicantForm({ districts }: { districts: District[] }) {
  const router = useRouter();
  const districtsByName = useMemo(
    () => new Map(districts.map((d) => [d.name, d.province])),
    [districts],
  );

  // demographics
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dob, setDob] = useState("");
  const [sex, setSex] = useState<Sex | "">("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [nid, setNid] = useState("");
  const [district, setDistrict] = useState("");
  const [ubudehe, setUbudehe] = useState<UbudeheCategory>(3);
  const [cbhi, setCbhi] = useState<CbhiStatus>("enrolled");

  // occupation
  const [occTitle, setOccTitle] = useState("");
  const [occClass, setOccClass] = useState<OccupationClass>("I");

  // vitals
  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [sbp, setSbp] = useState("");
  const [dbp, setDbp] = useState("");

  // lifestyle
  const [tobacco, setTobacco] = useState<Tobacco>("none");
  const [alcohol, setAlcohol] = useState("0");
  const [exercise, setExercise] = useState("3");

  // coverage
  const [sumInsured, setSumInsured] = useState("5000000");
  const [history, setHistory] = useState("");

  // documents
  const [files, setFiles] = useState<File[]>([]);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const province = district ? (districtsByName.get(district) ?? "") : "";

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
        alcohol_units_per_week: Number(alcohol) || 0,
        exercise_days_per_week: Number(exercise) || 0,
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
      sum_insured_rwf: Number(sumInsured),
      medical_docs: [],
    };
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!sex) {
      setError("Please select sex.");
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
    <form onSubmit={onSubmit} className="space-y-8">
      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      ) : null}

      <Section title="Applicant">
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
              <option value="M">M</option>
              <option value="F">F</option>
            </select>
          </label>
          <label>
            <Label label="Email" required />
            <input
              type="email"
              className={inputCls}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </label>
          <label>
            <Label label="Phone" hint="optional, E.164" />
            <input
              type="tel"
              className={inputCls}
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+250788000000"
              autoComplete="tel"
            />
          </label>
          <label className="col-span-2">
            <Label label="National ID" hint="exactly 16 digits" required />
            <input
              className={inputCls}
              value={nid}
              onChange={(e) => setNid(e.target.value.replace(/\D/g, "").slice(0, 16))}
              pattern="\d{16}"
              minLength={16}
              maxLength={16}
              required
              inputMode="numeric"
            />
          </label>
        </div>
      </Section>

      <Section title="Location">
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
          </label>
          <label>
            <Label label="Province" hint="auto-filled" />
            <input className={inputCls} value={province} readOnly tabIndex={-1} />
          </label>
          <label>
            <Label label="Ubudehe category" />
            <select
              className={selectCls}
              value={String(ubudehe)}
              onChange={(e) => setUbudehe(Number(e.target.value) as UbudeheCategory)}
            >
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
              <option value="4">4</option>
            </select>
          </label>
          <label>
            <Label label="CBHI status" />
            <select
              className={selectCls}
              value={cbhi}
              onChange={(e) => setCbhi(e.target.value as CbhiStatus)}
            >
              <option value="enrolled">enrolled</option>
              <option value="lapsed">lapsed</option>
              <option value="not_applicable">not applicable</option>
            </select>
          </label>
        </div>
      </Section>

      <Section title="Occupation">
        <div className="grid grid-cols-[1fr_120px] gap-3">
          <label>
            <Label label="Title" required />
            <input
              className={inputCls}
              value={occTitle}
              onChange={(e) => setOccTitle(e.target.value)}
              placeholder="e.g. Software engineer"
              required
            />
          </label>
          <label>
            <Label label="Class" required />
            <select
              className={selectCls}
              value={occClass}
              onChange={(e) => setOccClass(e.target.value as OccupationClass)}
            >
              <option value="I">I — office</option>
              <option value="II">II — manual</option>
              <option value="III">III — hazardous</option>
            </select>
          </label>
        </div>
      </Section>

      <Section title="Vitals">
        <div className="grid grid-cols-4 gap-3">
          <label>
            <Label label="Height (cm)" required />
            <input
              type="number"
              className={inputCls}
              value={heightCm}
              onChange={(e) => setHeightCm(e.target.value)}
              min={50}
              max={250}
              step="0.1"
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
              step="0.1"
              required
            />
          </label>
          <label>
            <Label label="SBP" hint="mmHg, optional" />
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
            <Label label="DBP" hint="mmHg, optional" />
            <input
              type="number"
              className={inputCls}
              value={dbp}
              onChange={(e) => setDbp(e.target.value)}
              min={40}
              max={150}
            />
          </label>
        </div>
      </Section>

      <Section title="Lifestyle">
        <div className="grid grid-cols-3 gap-3">
          <label>
            <Label label="Tobacco" />
            <select
              className={selectCls}
              value={tobacco}
              onChange={(e) => setTobacco(e.target.value as Tobacco)}
            >
              <option value="none">none</option>
              <option value="occasional">occasional</option>
              <option value="daily">daily</option>
            </select>
          </label>
          <label>
            <Label label="Alcohol (units/wk)" />
            <input
              type="number"
              className={inputCls}
              value={alcohol}
              onChange={(e) => setAlcohol(e.target.value)}
              min={0}
              max={100}
            />
          </label>
          <label>
            <Label label="Exercise (days/wk)" />
            <input
              type="number"
              className={inputCls}
              value={exercise}
              onChange={(e) => setExercise(e.target.value)}
              min={0}
              max={7}
            />
          </label>
        </div>
      </Section>

      <Section title="Coverage">
        <div className="space-y-3">
          <label className="block">
            <Label label="Sum insured (RWF)" required />
            <input
              type="number"
              className={inputCls}
              value={sumInsured}
              onChange={(e) => setSumInsured(e.target.value)}
              min={500000}
              max={500000000}
              step="100000"
              required
            />
          </label>
          <label className="block">
            <Label label="Declared history" hint="one condition per line, optional" />
            <textarea
              className={`${inputCls} font-mono text-xs`}
              rows={3}
              value={history}
              onChange={(e) => setHistory(e.target.value)}
              placeholder="hypertension&#10;type 2 diabetes"
            />
          </label>
        </div>
      </Section>

      <Section title="Medical documents">
        <label className="block">
          <Label label="PDFs" hint="optional, one or more" />
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
                <li key={f.name}>{f.name} · {(f.size / 1024).toFixed(1)} KB</li>
              ))}
            </ul>
          ) : null}
        </label>
      </Section>

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
