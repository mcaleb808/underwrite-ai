"use client";

import { useEffect, useState } from "react";

import type { RiskBand } from "@/lib/types";

import { BandPill } from "./BandPill";

function polar(cx: number, cy: number, r: number, a: number) {
  return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
}

function describeArc(cx: number, cy: number, r: number, start: number, end: number) {
  const s = polar(cx, cy, r, start);
  const e = polar(cx, cy, r, end);
  const large = end - start > Math.PI ? 1 : 0;
  return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`;
}

function colorForBand(band: RiskBand | null | undefined): string {
  if (band === "low") return "var(--good)";
  if (band === "high" || band === "very_high") return "var(--bad)";
  return "var(--warn)";
}

export function RiskArc({
  score,
  band,
}: {
  score: number;
  band: RiskBand | null | undefined;
}) {
  const target = Math.max(0, Math.min(100, score));
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    let raf = 0;
    let start: number | null = null;
    const animate = (t: number) => {
      if (start === null) start = t;
      const p = Math.min(1, (t - start) / 1200);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(target * eased);
      if (p < 1) raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [target]);

  const r = 78;
  const cx = 100;
  const cy = 100;
  const startAngle = Math.PI * 0.85;
  const endAngle = Math.PI * 2.15;
  const total = endAngle - startAngle;
  const len = Math.PI * 2 * r;
  const arcLen = (total / (Math.PI * 2)) * len;
  const fillFrac = display / 100;
  const offset = arcLen * (1 - fillFrac);
  const arcPath = describeArc(cx, cy, r, startAngle, endAngle);
  const color = colorForBand(band);

  return (
    <div className="rounded border border-line bg-paper px-5 py-6 text-center">
      <div className="field-label mb-3">Risk score</div>
      <div className="relative h-[130px]">
        <svg
          width="200"
          height="130"
          viewBox="0 0 200 130"
          className="mx-auto block"
        >
          <path d={arcPath} className="arc-track" strokeWidth={10} />
          <path
            d={arcPath}
            className="arc-fill"
            stroke={color}
            strokeWidth={10}
            strokeDasharray={`${arcLen} ${arcLen}`}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="pointer-events-none absolute inset-x-0 top-9 text-center">
          <div className="serif tnum text-[52px] leading-none">
            {display.toFixed(1)}
          </div>
          <div className="mono mt-0.5 text-[10px] text-muted">OF 100</div>
        </div>
      </div>
      <div className="mt-2">
        <BandPill band={band ?? null} />
      </div>
    </div>
  );
}
