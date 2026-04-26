import type { StepState, StepStatus } from "@/lib/pipeline";

function StatusIcon({ status }: { status: StepStatus }) {
  if (status === "active") {
    return (
      <span aria-hidden className="relative inline-flex h-5 w-5 items-center justify-center">
        <span className="pulse-dot" />
      </span>
    );
  }
  if (status === "done") {
    return (
      <span
        aria-hidden
        className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-ink text-paper"
      >
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" className="h-3 w-3">
          <path d="M3.5 8.5l3 3 6-6" />
        </svg>
      </span>
    );
  }
  if (status === "error") {
    return (
      <span
        aria-hidden
        className="inline-flex h-5 w-5 items-center justify-center rounded-full text-paper"
        style={{ background: "var(--bad)" }}
      >
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" className="h-3 w-3">
          <path d="M5 5l6 6M11 5l-6 6" />
        </svg>
      </span>
    );
  }
  return (
    <span
      aria-hidden
      className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-line-2 bg-paper"
    />
  );
}

function cardStyle(status: StepStatus): React.CSSProperties {
  if (status === "active") {
    return {
      borderColor: "color-mix(in oklch, var(--accent) 40%, var(--line))",
      background: "var(--paper)",
      boxShadow: "inset 3px 0 0 var(--accent)",
    };
  }
  if (status === "error") {
    return {
      borderColor: "color-mix(in oklch, var(--bad) 30%, var(--line))",
      background: "color-mix(in oklch, var(--bad) 6%, var(--paper))",
    };
  }
  return { borderColor: "var(--line)", background: "var(--paper)" };
}

export function Timeline({
  steps,
  finalized,
  failed,
}: {
  steps: StepState[];
  finalized: boolean;
  failed: boolean;
}) {
  const allPending = steps.every((s) => s.status === "pending");
  const hasError = steps.some((s) => s.status === "error") || failed;

  return (
    <ol className="space-y-2">
      {steps.map((step, i) => {
        const isLast = i === steps.length - 1;
        const isPending = step.status === "pending";
        const isError = step.status === "error";
        return (
          <li key={step.key} className="grid grid-cols-[24px_1fr] gap-x-3">
            <div className="relative flex flex-col items-center">
              {!isLast ? (
                <span
                  aria-hidden
                  className="absolute left-1/2 top-7 -translate-x-1/2 bg-line"
                  style={{ bottom: "-12px", width: 1 }}
                />
              ) : null}
              <div className="relative flex h-7 items-center">
                <StatusIcon status={step.status} />
              </div>
            </div>
            <div className="rounded border px-4 py-2.5" style={cardStyle(step.status)}>
              <div className="flex items-baseline justify-between gap-3">
                <h3
                  className={`serif text-[16px] tracking-[-0.005em] ${
                    isPending ? "text-muted-2" : isError ? "text-[color:var(--bad)]" : "text-ink"
                  }`}
                >
                  {step.label}
                </h3>
                {step.reruns > 0 ? (
                  <span className="chip mono shrink-0" style={{ fontSize: 10 }}>
                    {step.reruns === 1 ? "1 rerun" : `${step.reruns} reruns`}
                  </span>
                ) : null}
              </div>
              <p
                className={`mt-0.5 text-[12px] leading-[1.5] ${
                  isPending ? "text-muted-2" : isError ? "text-[color:var(--bad)]" : "text-muted"
                }`}
              >
                {isError
                  ? step.errorMessage ?? "This step couldn't complete."
                  : step.summary ?? step.description}
              </p>
              {step.hasIssues && step.status === "done" ? (
                <p className="mt-1 text-[12px]" style={{ color: "var(--warn)" }}>
                  A reviewer should double-check the flagged concerns.
                </p>
              ) : null}
            </div>
          </li>
        );
      })}

      {allPending ? (
        <p className="pt-2 text-center text-[12px] text-muted">
          Waiting for the pipeline to start…
        </p>
      ) : hasError ? (
        <p className="pt-2 text-center text-[12px]" style={{ color: "var(--bad)" }}>
          Pipeline stopped before producing a decision - re-run this case to try again.
        </p>
      ) : finalized ? (
        <p className="pt-2 text-center text-[12px]" style={{ color: "var(--good)" }}>
          Pipeline finished - see your decision below.
        </p>
      ) : null}
    </ol>
  );
}
