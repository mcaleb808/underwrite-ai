import type { Verdict } from "@/lib/types";

const META: Record<Verdict, { label: string; color: string }> = {
  accept:                 { label: "Accept",                 color: "var(--good)" },
  accept_with_conditions: { label: "Accept with conditions", color: "var(--warn)" },
  refer:                  { label: "Refer to senior",        color: "var(--ink)"  },
  decline:                { label: "Decline",                color: "var(--bad)"  },
};

export function VerdictText({ verdict }: { verdict: Verdict | null | undefined }) {
  if (!verdict) {
    return <span className="text-[13px] text-muted">—</span>;
  }
  const m = META[verdict] ?? { label: verdict, color: "var(--ink)" };
  return (
    <span className="text-[13px] font-medium" style={{ color: m.color }}>
      {m.label}
    </span>
  );
}
