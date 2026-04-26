"use client";

import { useState } from "react";

import type { ApplicationStatus, Verdict } from "@/lib/types";

type Tone = "good" | "warn" | "bad" | "ink";

type VerdictCopy = {
  headline: string;
  subject: string;
  tone: Tone;
};

const VERDICT_COPY: Record<Verdict, VerdictCopy> = {
  accept: {
    headline: "approved",
    subject: "Your health coverage application has been approved",
    tone: "good",
  },
  accept_with_conditions: {
    headline: "approved with conditions",
    subject: "Your health coverage application has been approved with conditions",
    tone: "warn",
  },
  refer: {
    headline: "referred to a senior underwriter",
    subject: "Your health coverage application is being reviewed",
    tone: "ink",
  },
  decline: {
    headline: "not approved at this tier",
    subject: "Your health coverage application - update",
    tone: "bad",
  },
};

const FAILED_STATUSES = new Set(["failed", "error", "bounced"]);

const TONE_VAR: Record<Tone, string> = {
  good: "var(--good)",
  warn: "var(--warn)",
  bad: "var(--bad)",
  ink: "var(--ink)",
};

function formatTime(ms: number): string {
  return new Date(ms).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function EmailReceipt({
  status,
  emailStatus,
  providerMessageId,
}: {
  status: ApplicationStatus;
  emailStatus: string;
  providerMessageId: string | null;
}) {
  // Capture once on first render so the receipt header doesn't drift
  // every time the parent re-renders during a subsequent run.
  const [approvedAt] = useState(() => Date.now());

  const decision = status.decision;
  if (!decision) return null;

  const copy =
    VERDICT_COPY[decision.verdict as Verdict] ?? {
      headline: decision.verdict.replace(/_/g, " "),
      subject: "Your health coverage application - update",
      tone: "ink" as Tone,
    };

  const emailFailed = FAILED_STATUSES.has(emailStatus.toLowerCase());
  const stripTone: Tone = emailFailed ? "bad" : copy.tone;
  const stripColor = TONE_VAR[stripTone];
  const headerLabel = emailFailed
    ? `Decision ${copy.headline} · email ${emailStatus} - delivery failed`
    : `Decision ${copy.headline} · email ${emailStatus}`;

  return (
    <div className="email-pop mt-7">
      <div
        className="flex flex-wrap items-center justify-between gap-3 rounded-t border px-5 py-3.5"
        style={{
          background: `color-mix(in oklch, ${stripColor} 12%, var(--paper))`,
          borderColor: `color-mix(in oklch, ${stripColor} 30%, var(--line))`,
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="grid h-7 w-7 place-items-center rounded-full text-paper"
            style={{ background: stripColor }}
          >
            {emailFailed ? (
              <svg
                width="14"
                height="14"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.4"
                strokeLinecap="round"
              >
                <path d="M8 4v5M8 11.5v.5" />
              </svg>
            ) : (
              <svg
                width="14"
                height="14"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.6"
                strokeLinecap="round"
              >
                <path d="M3.5 8.5l3 3 6-6" />
              </svg>
            )}
          </div>
          <div>
            <div className="text-[14px] font-semibold">{headerLabel}</div>
            <div className="mono mt-0.5 text-[11px] text-muted">
              POST /api/v1/applications/{status.reference_number}/approve · 200 OK ·{" "}
              {formatTime(approvedAt)}
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-b border border-t-0 border-line bg-paper">
        <div
          className="grid gap-y-1.5 px-6 py-4 text-[13px]"
          style={{
            gridTemplateColumns: "70px 1fr",
            columnGap: 12,
            borderBottom: "1px solid var(--line)",
          }}
        >
          <span className="field-label self-center">From</span>
          <span>
            <span className="font-medium">UnderwriteAI</span>{" "}
            <span className="text-muted">&lt;noreply@underwrite.ai&gt;</span>
          </span>
          <span className="field-label self-center">To</span>
          <span className="text-muted">applicant on file</span>
          <span className="field-label self-center">Subject</span>
          <span className="font-medium">
            {copy.subject} - {status.reference_number}
          </span>
        </div>

        <div className="px-7 py-6 text-[14px] leading-[1.65] text-ink-2">
          <p className="m-0 mb-3.5">Hello,</p>
          <p className="m-0 mb-3.5">
            Your health coverage application{" "}
            <span className="mono text-[12px]">{status.reference_number}</span> has been{" "}
            <strong className="text-ink">{copy.headline}</strong>.
          </p>

          {decision.premium_loading_pct > 0 ? (
            <p className="m-0 mb-3.5">
              Your premium will be{" "}
              <strong>{decision.premium_loading_pct.toFixed(1)}% higher</strong>{" "}
              than the standard rate.
            </p>
          ) : null}

          {decision.conditions.length > 0 ? (
            <>
              <p className="m-0 mb-2 font-medium text-ink">
                {decision.conditions.length === 1
                  ? "One condition to confirm before activation:"
                  : `${decision.conditions.length} conditions to confirm before activation:`}
              </p>
              <ol className="m-0 mb-4 pl-6">
                {decision.conditions.map((c, i) => (
                  <li key={i} className="mb-1.5">
                    {c}
                  </li>
                ))}
              </ol>
            </>
          ) : null}

          {decision.reasoning ? (
            <p className="m-0 mb-3.5">{decision.reasoning}</p>
          ) : null}

          <p className="m-0 mb-1">Welcome aboard,</p>
          <p className="m-0">The UnderwriteAI team</p>
        </div>

        <div
          className="flex flex-wrap items-center justify-between gap-3 px-6 py-3 text-[10px]"
          style={{ background: "var(--paper-2)", borderTop: "1px solid var(--line)" }}
        >
          <span className="mono text-muted">
            {emailFailed
              ? `Delivery failed · ${emailStatus}`
              : `Delivered · message-id ${providerMessageId ?? "—"}`}
          </span>
          <span className="text-muted">
            Approved by {status.approved_by ?? "underwriter"}
          </span>
        </div>
      </div>
    </div>
  );
}
