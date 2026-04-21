export function FailureCard({ taskId }: { taskId: string }) {
  return (
    <section className="overflow-hidden rounded-xl border-2 border-red-200 bg-white dark:border-red-900 dark:bg-zinc-950">
      <div className="bg-red-50 px-6 py-5 dark:bg-red-950/40">
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-red-500 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white">
            No decision
          </span>
          <span className="text-xs uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Pipeline stopped
          </span>
        </div>
        <h2 className="mt-3 text-lg font-semibold leading-snug text-zinc-900 dark:text-zinc-50">
          We couldn&apos;t complete this decision.
        </h2>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          The underwriting pipeline encountered an error and stopped before reaching a
          verdict. The timeline above shows which step failed.
        </p>
      </div>
      <div className="px-6 py-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          What you can do
        </h3>
        <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300 marker:text-red-400">
          <li>
            Re-run this case from the persona picker — most failures are transient and
            clear on the second attempt.
          </li>
          <li>
            If the same step fails twice, check the AI provider&apos;s status page or the
            server logs for this task.
          </li>
        </ul>
        <p className="mt-3 font-mono text-[11px] text-zinc-400 dark:text-zinc-600">
          task id · {taskId}
        </p>
      </div>
    </section>
  );
}
