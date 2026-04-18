import Link from "next/link";

import { listApplications } from "@/lib/api";

const STATUS_STYLES: Record<string, string> = {
  queued: "bg-zinc-100 text-zinc-600",
  running: "bg-blue-100 text-blue-700",
  awaiting_review: "bg-amber-100 text-amber-700",
  modified: "bg-purple-100 text-purple-700",
  reeval: "bg-blue-100 text-blue-700",
  approved: "bg-emerald-100 text-emerald-700",
  sent: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export async function RecentApplications() {
  const items = await listApplications(10);
  if (items.length === 0) return null;

  return (
    <section className="mt-10">
      <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        Recent applications
      </h2>
      <ul className="divide-y divide-zinc-200 rounded-lg border border-zinc-200 bg-white dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-950">
        {items.map((item) => (
          <li key={item.task_id}>
            <Link
              href={`/applications/${item.task_id}`}
              className="flex items-center justify-between gap-4 px-5 py-3 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-900"
            >
              <div className="min-w-0">
                <div className="flex items-baseline gap-2">
                  <span className="font-mono text-xs text-zinc-500 dark:text-zinc-400">
                    {item.reference_number}
                  </span>
                  <span className="text-zinc-700 dark:text-zinc-300">{item.applicant_id}</span>
                </div>
                <div className="text-xs text-zinc-500 dark:text-zinc-400">
                  {formatDate(item.created_at)}
                  {item.risk_score !== null
                    ? ` · risk ${item.risk_score} (${item.risk_band})`
                    : ""}
                </div>
              </div>
              <div className="flex items-center gap-2 text-xs">
                {item.verdict ? (
                  <span className="text-zinc-600 dark:text-zinc-300">
                    {item.verdict.replace(/_/g, " ")}
                  </span>
                ) : null}
                <span
                  className={`rounded-full px-2 py-0.5 ${
                    STATUS_STYLES[item.status] ?? "bg-zinc-100 text-zinc-600"
                  }`}
                >
                  {item.status}
                </span>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
