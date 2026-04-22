"use client";

import { useState } from "react";

import { approveDecision, getApplication, modifyDecision, reevaluate } from "@/lib/api";
import type { ApplicationStatus, Verdict } from "@/lib/types";

const VERDICTS: Verdict[] = ["accept", "accept_with_conditions", "refer", "decline"];

const FINAL_STATUSES = new Set(["sent", "approved"]);

export function ReviewActions({
  status,
  onChange,
}: {
  status: ApplicationStatus;
  onChange: (next: ApplicationStatus) => void;
}) {
  const decision = status.decision;
  const [editing, setEditing] = useState(false);
  const [verdict, setVerdict] = useState<Verdict>(
    (decision?.verdict as Verdict) ?? "accept",
  );
  const [loading, setLoading] = useState(decision?.premium_loading_pct ?? 0);
  const [conditions, setConditions] = useState(
    (decision?.conditions ?? []).join("\n"),
  );
  const [reasoning, setReasoning] = useState(decision?.reasoning ?? "");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [emailNotice, setEmailNotice] = useState<string | null>(null);

  if (!decision) return null;
  const isFinal = FINAL_STATUSES.has(status.status);

  async function onSaveModify() {
    setBusy("modify");
    setError(null);
    try {
      const next = await modifyDecision(status.task_id, {
        verdict,
        premium_loading_pct: loading,
        conditions: conditions
          .split("\n")
          .map((c) => c.trim())
          .filter(Boolean),
        reasoning,
      });
      onChange(next);
      setEditing(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "unknown error");
    } finally {
      setBusy(null);
    }
  }

  async function onApprove() {
    setBusy("approve");
    setError(null);
    setEmailNotice(null);
    try {
      const result = await approveDecision(status.task_id, "underwriter@demo");
      setEmailNotice(`email: ${result.email_status} (${result.provider_message_id ?? "—"})`);
      onChange(await getApplication(status.task_id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "unknown error");
    } finally {
      setBusy(null);
    }
  }

  async function onReeval() {
    setBusy("reeval");
    setError(null);
    try {
      await reevaluate(status.task_id);
      // page-level Live component will refresh on next 'closed' event
      onChange({ ...status, status: "reeval", decision: null });
    } catch (e) {
      setError(e instanceof Error ? e.message : "unknown error");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          Review
        </h2>
        {isFinal ? (
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
            sent · approved by {status.approved_by ?? "?"}
          </span>
        ) : null}
      </header>

      {editing ? (
        <div className="space-y-3 text-sm">
          <label className="block">
            <span className="text-xs text-zinc-500">Verdict</span>
            <select
              value={verdict}
              onChange={(e) => setVerdict(e.target.value as Verdict)}
              className="mt-1 w-full rounded-md border border-zinc-200 bg-white px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
            >
              {VERDICTS.map((v) => (
                <option key={v} value={v}>
                  {v.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-xs text-zinc-500">Premium loading (%)</span>
            <input
              type="number"
              value={loading}
              step="0.5"
              onChange={(e) => setLoading(Number(e.target.value))}
              className="mt-1 w-full rounded-md border border-zinc-200 bg-white px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>
          <label className="block">
            <span className="text-xs text-zinc-500">Conditions (one per line)</span>
            <textarea
              value={conditions}
              onChange={(e) => setConditions(e.target.value)}
              rows={3}
              className="mt-1 w-full rounded-md border border-zinc-200 bg-white px-2 py-1 font-mono text-xs dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>
          <label className="block">
            <span className="text-xs text-zinc-500">Reasoning</span>
            <textarea
              value={reasoning}
              onChange={(e) => setReasoning(e.target.value)}
              rows={5}
              className="mt-1 w-full rounded-md border border-zinc-200 bg-white px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onSaveModify}
              disabled={busy === "modify"}
              className="rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-white dark:text-zinc-900"
            >
              {busy === "modify" ? "saving…" : "save changes"}
            </button>
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="rounded-md border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
            >
              cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onApprove}
            disabled={busy !== null || isFinal}
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {busy === "approve" ? "sending…" : "approve & send email"}
          </button>
          <button
            type="button"
            onClick={() => setEditing(true)}
            disabled={busy !== null || isFinal}
            className="rounded-md border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
          >
            modify
          </button>
          <button
            type="button"
            onClick={onReeval}
            disabled={busy !== null || isFinal}
            className="rounded-md border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
          >
            {busy === "reeval" ? "queuing…" : "re-evaluate"}
          </button>
        </div>
      )}

      {emailNotice ? (
        <p className="mt-3 text-xs text-emerald-600 dark:text-emerald-400">{emailNotice}</p>
      ) : null}
      {error ? (
        <p className="mt-3 text-xs text-red-600 dark:text-red-400">{error}</p>
      ) : null}
    </section>
  );
}
