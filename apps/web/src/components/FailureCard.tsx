export function FailureCard({ taskId }: { taskId: string }) {
  return (
    <article className="overflow-hidden rounded border border-line bg-paper">
      <div
        className="px-7 py-6"
        style={{
          background: "color-mix(in oklch, var(--bad) 8%, var(--paper))",
          borderBottom: "1px solid var(--line)",
        }}
      >
        <span
          className="chip"
          style={{ background: "var(--bad)", color: "white", borderColor: "var(--bad)" }}
        >
          No decision
        </span>
        <h2 className="serif mt-4 mb-1.5 text-[26px] leading-[1.15] tracking-[-0.01em]">
          We couldn&apos;t complete this decision.
        </h2>
        <p className="m-0 text-[14px] leading-[1.55] text-muted">
          The pipeline encountered an error and stopped before reaching a verdict.
          The timeline above shows which step failed.
        </p>
      </div>
      <div className="px-7 py-6">
        <div className="field-label mb-2.5">What you can do</div>
        <ul className="m-0 list-disc space-y-1.5 pl-5 text-[14px] leading-[1.6] text-ink-2">
          <li>
            Re-run this case from the persona picker - most failures are transient and
            clear on the second attempt.
          </li>
          <li>
            If the same step fails twice, check the AI provider&apos;s status page or the
            server logs for this task.
          </li>
        </ul>
        <p className="mono mt-4 text-[11px] text-muted">task id · {taskId}</p>
      </div>
    </article>
  );
}
