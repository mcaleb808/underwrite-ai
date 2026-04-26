"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { BandPill } from "@/components/ui/BandPill";
import { VerdictText } from "@/components/ui/VerdictText";
import { useConfirm, useToast } from "@/components/ui/providers";
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

function formatRelative(iso: string): string {
  const t = new Date(iso).getTime();
  const diff = Date.now() - t;
  const m = Math.floor(diff / 60_000);
  if (m < 1) return "just now";
  if (m < 60) return `${m} min ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} h ago`;
  const d = Math.floor(h / 24);
  return `${d} d ago`;
}

function matchesTab(tab: TabKey, status: string): boolean {
  if (tab === "all") return true;
  return STATUS_BY_TAB[tab].has(status);
}

function prettyName(applicantId: string): string {
  return applicantId
    .split("-")
    .filter((part) => !/^\d/.test(part))
    .map((p) => (p && p[0] ? p[0].toUpperCase() + p.slice(1) : ""))
    .join(" ")
    .trim() || applicantId;
}

export function RecentApplicationsList({ items }: { items: ApplicationListItem[] }) {
  const router = useRouter();
  const confirm = useConfirm();
  const toast = useToast();
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
    const ok = await confirm({
      title: "Clear all finished applications?",
      message:
        "This permanently deletes their events and decisions. In-flight runs are kept.",
      confirmLabel: "Clear",
      tone: "destructive",
    });
    if (!ok) return;
    setClearing(true);
    try {
      await clearTerminalApplications();
      toast.success("Finished applications cleared.");
      router.refresh();
    } catch (err) {
      toast.error(`Couldn't clear: ${String(err)}`);
    } finally {
      setClearing(false);
    }
  }

  return (
    <section>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <h2 className="serif m-0 text-[24px] tracking-[-0.01em]">
          Recent decisions
        </h2>
        <button
          type="button"
          onClick={handleClear}
          disabled={clearing || !hasTerminal}
          className="btn ghost text-[12px]"
          style={{ border: "1px solid var(--line-2)", padding: "6px 12px" }}
        >
          {clearing ? "Clearing…" : "Clear finished"}
        </button>
      </div>

      <div className="mb-4 flex flex-wrap gap-1.5">
        {(Object.keys(TAB_LABELS) as TabKey[]).map((key) => {
          const active = tab === key;
          const count = counts[key];
          return (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={active ? "chip solid" : "chip"}
            >
              {TAB_LABELS[key]}
              <span
                className="tnum"
                style={{
                  fontSize: 10,
                  opacity: active ? 0.75 : 0.6,
                  marginLeft: 2,
                }}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {filtered.length === 0 ? (
        <p className="rounded border border-dashed border-line-2 bg-paper px-5 py-6 text-center text-[12px] text-muted">
          No applications in this view.
        </p>
      ) : (
        <div className="overflow-hidden rounded border border-line bg-paper">
          <div
            className="hidden grid-cols-[170px_1.4fr_80px_110px_1fr_90px] gap-4 border-b border-line px-5 py-3 sm:grid"
            style={{ fontSize: 10, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}
          >
            <div>Reference</div>
            <div>Applicant</div>
            <div>Score</div>
            <div>Band</div>
            <div>Verdict</div>
            <div className="text-right">When</div>
          </div>
          <ul className="m-0 list-none p-0">
            {filtered.map((item, i) => (
              <li
                key={item.task_id}
                className={i < filtered.length - 1 ? "border-b border-line" : ""}
              >
                <Link
                  href={`/applications/${item.task_id}`}
                  className="grid grid-cols-1 gap-2 px-5 py-3.5 text-[13px] hover:bg-paper-2 sm:grid-cols-[170px_1.4fr_80px_110px_1fr_90px] sm:items-center sm:gap-4"
                >
                  <div className="mono text-[11px] text-muted">{item.reference_number}</div>
                  <div className="font-medium">{prettyName(item.applicant_id)}</div>
                  <div className="serif tnum text-[16px]">
                    {item.risk_score !== null ? item.risk_score.toFixed(1) : "—"}
                  </div>
                  <div>
                    <BandPill band={item.risk_band} />
                  </div>
                  <div>
                    <VerdictText verdict={item.verdict} />
                  </div>
                  <div className="text-[12px] text-muted sm:text-right">
                    {formatRelative(item.created_at)}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
