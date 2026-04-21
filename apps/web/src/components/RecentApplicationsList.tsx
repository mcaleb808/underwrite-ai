"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { clearTerminalApplications } from "@/lib/api";
import type { ApplicationListItem } from "@/lib/types";

type TabKey = "all" | "running" | "awaiting" | "approved" | "failed";

const STATUS_BY_TAB: Record<TabKey, ReadonlySet<string>> = {
  all: new Set(),
  running: new Set(["queued", "running", "reeval"]),
  awaiting: new Set(["awaiting_review", "modified"]),
  approved: new Set(["approved", "sent"]),
  failed: new Set(["failed", "cancelled"]),
};

const TAB_LABELS: Record<TabKey, string> = {
  all: "All",
  running: "Running",
  awaiting: "Awaiting review",
  approved: "Approved",
  failed: "Failed",
};

const STATUS_STYLES: Record<string, string> = {
  queued: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
  running: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  awaiting_review: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  modified: "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
  reeval: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  approved: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  sent: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  failed: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
  cancelled: "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function matchesTab(tab: TabKey, status: string): boolean {
  if (tab === "all") return true;
  return STATUS_BY_TAB[tab].has(status);
}

export function RecentApplicationsList({ items }: { items: ApplicationListItem[] }) {
  const router = useRouter();
  const [tab, setTab] = useState<TabKey>("all");
  const [clearing, setClearing] = useState(false);

  const counts = useMemo(() => {
    const out: Record<TabKey, number> = {
      all: items.length,
      running: 0,
      awaiting: 0,
      approved: 0,
      failed: 0,
    };
    for (const it of items) {
      for (const key of ["running", "awaiting", "approved", "failed"] as const) {
        if (STATUS_BY_TAB[key].has(it.status)) out[key] += 1;
      }
    }
    return out;
  }, [items]);

  const filtered = useMemo(
    () => items.filter((it) => matchesTab(tab, it.status)),
    [items, tab],
  );

  const hasTerminal = counts.awaiting + counts.approved + counts.failed > 0;

  async function handleClear() {
    if (
      !window.confirm(
        "Clear all finished applications? This permanently deletes their events and decisions. In-flight runs are kept.",
      )
    ) {
      return;
    }
    setClearing(true);
    try {
      await clearTerminalApplications();
      router.refresh();
    } catch (err) {
      window.alert(`Couldn't clear: ${String(err)}`);
    } finally {
      setClearing(false);
    }
  }

  return (
    <section className="mt-10">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          Recent applications
        </h2>
        <button
          type="button"
          onClick={handleClear}
          disabled={clearing || !hasTerminal}
          className="rounded-md border border-zinc-300 bg-white px-3 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-300 dark:hover:bg-zinc-900"
        >
          {clearing ? "Clearing…" : "Clear finished"}
        </button>
      </div>

      <div className="mb-3 flex flex-wrap gap-1 border-b border-zinc-200 dark:border-zinc-800">
        {(Object.keys(TAB_LABELS) as TabKey[]).map((key) => {
          const active = tab === key;
          const count = counts[key];
          return (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={`-mb-px border-b-2 px-3 py-1.5 text-xs font-medium transition-colors ${
                active
                  ? "border-zinc-900 text-zinc-900 dark:border-zinc-50 dark:text-zinc-50"
                  : "border-transparent text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
              }`}
            >
              {TAB_LABELS[key]}
              <span
                className={`ml-1.5 rounded-full px-1.5 py-0.5 text-[10px] font-semibold tabular-nums ${
                  active
                    ? "bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900"
                    : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {filtered.length === 0 ? (
        <p className="rounded-lg border border-dashed border-zinc-200 bg-zinc-50/50 px-5 py-6 text-center text-xs text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900/40 dark:text-zinc-400">
          No applications in this view.
        </p>
      ) : (
        <ul className="divide-y divide-zinc-200 rounded-lg border border-zinc-200 bg-white dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-950">
          {filtered.map((item) => (
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
                      STATUS_STYLES[item.status] ??
                      "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
                    }`}
                  >
                    {item.status.replace(/_/g, " ")}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
