"use client";

import { useState } from "react";

import { approveDecision, getApplication, modifyDecision } from "@/lib/api";
import type { ApplicationStatus, Verdict } from "@/lib/types";

const VERDICTS: Verdict[] = ["accept", "accept_with_conditions", "refer", "decline"];
const FINAL_STATUSES = new Set(["sent", "approved"]);

export type ApproveResult = {
  email_status: string;
  provider_message_id: string | null;
};

export function ReviewActions({
  status,
  onChange,
  onApproved,
  onReevaluate,
}: {
  status: ApplicationStatus;
  onChange: (next: ApplicationStatus) => void;
  onApproved?: (result: ApproveResult) => void;
  onReevaluate: () => Promise<void>;
}) {
  const decision = status.decision;
  const [editing, setEditing] = useState(false);
  const [verdict, setVerdict] = useState<Verdict>(
    (decision?.verdict as Verdict) ?? "accept",
  );
  const [loading, setLoading] = useState(decision?.premium_loading_pct ?? 0);
  const [conditions, setConditions] = useState((decision?.conditions ?? []).join("\n"));
  const [reasoning, setReasoning] = useState(decision?.reasoning ?? "");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
    try {
      const result = await approveDecision(status.task_id, "underwriter@demo");
      onApproved?.({
        email_status: result.email_status,
        provider_message_id: result.provider_message_id,
      });
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
      await onReevaluate();
    } catch (e) {
      setError(e instanceof Error ? e.message : "unknown error");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="mt-5">
      {editing ? (
        <div className="rounded border border-line bg-paper p-5 space-y-5">
          <div className="field-label">Modify decision</div>
          <label className="block">
            <div className="field-label">Verdict</div>
            <select
              value={verdict}
              onChange={(e) => setVerdict(e.target.value as Verdict)}
              className="field"
            >
              {VERDICTS.map((v) => (
                <option key={v} value={v}>
                  {v.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <div className="field-label">Premium loading (%)</div>
            <input
              type="number"
              value={loading}
              step="0.5"
              onChange={(e) => setLoading(Number(e.target.value))}
              className="field"
            />
          </label>
          <label className="block">
            <div className="field-label">Conditions (one per line)</div>
            <textarea
              value={conditions}
              onChange={(e) => setConditions(e.target.value)}
              rows={3}
              className="field mono text-[12px]"
            />
          </label>
          <label className="block">
            <div className="field-label">Reasoning</div>
            <textarea
              value={reasoning}
              onChange={(e) => setReasoning(e.target.value)}
              rows={5}
              className="field"
            />
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onSaveModify}
              disabled={busy === "modify"}
              className="btn"
            >
              {busy === "modify" ? "Saving…" : "Save changes"}
            </button>
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="btn ghost"
              style={{ border: "1px solid var(--line-2)" }}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div
          className="flex flex-wrap gap-2.5 rounded-b border border-t-0 border-line px-7 py-4 -mt-px"
          style={{ background: "var(--paper-2)" }}
        >
          <button
            type="button"
            onClick={onApprove}
            disabled={busy !== null || isFinal}
            className="btn"
          >
            {busy === "approve" ? (
              <>
                <span className="pulse-dot" />
                Sending email…
              </>
            ) : isFinal ? (
              "✓ Approved"
            ) : (
              "Approve & notify applicant"
            )}
          </button>
          <button
            type="button"
            onClick={() => setEditing(true)}
            disabled={busy !== null || isFinal}
            className="btn ghost"
            style={{ border: "1px solid var(--line-2)" }}
          >
            Modify
          </button>
          <button
            type="button"
            onClick={onReeval}
            disabled={busy !== null || isFinal}
            className="btn ghost"
            style={{ border: "1px solid var(--line-2)" }}
          >
            {busy === "reeval" ? "Queuing…" : "Re-evaluate"}
          </button>
        </div>
      )}

      {error ? (
        <p className="mt-3 text-[12px]" style={{ color: "var(--bad)" }}>
          {error}
        </p>
      ) : null}
    </section>
  );
}
