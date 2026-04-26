import type { RiskBand } from "@/lib/types";

const META: Record<RiskBand, { label: string; color: string }> = {
  low:       { label: "Low",       color: "var(--good)" },
  moderate:  { label: "Moderate",  color: "var(--warn)" },
  high:      { label: "High",      color: "var(--bad)"  },
  very_high: { label: "Very high", color: "var(--bad)"  },
};

export function BandPill({ band }: { band: RiskBand | null | undefined }) {
  if (!band) return null;
  const m = META[band];
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[11px] font-medium"
      style={{ color: m.color }}
    >
      <span
        aria-hidden
        className="inline-block h-1.5 w-1.5 rounded-full"
        style={{ background: m.color }}
      />
      {m.label}
    </span>
  );
}
