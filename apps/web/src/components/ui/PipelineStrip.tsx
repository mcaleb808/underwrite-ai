import type { StepState } from "@/lib/pipeline";

import { PipelineNode, type NodeStatus } from "./PipelineNode";

function nodeStatusFor(s: StepState): NodeStatus {
  if (s.status === "error") return "error";
  if (s.status === "done") return "done";
  if (s.status === "active") return "active";
  return "pending";
}

function captionFor(s: StepState): string {
  if (s.status === "error") return "failed";
  if (s.status === "done") return "✓ done";
  if (s.status === "active") return "running…";
  return "queued";
}

export function PipelineStrip({ steps }: { steps: StepState[] }) {
  return (
    <div className="relative grid grid-cols-5 gap-3">
      <div
        aria-hidden
        className="absolute left-[10%] right-[10%] top-[23px] h-px bg-line-2"
      />
      {steps.map((s, i) => {
        const status = nodeStatusFor(s);
        const caption = captionFor(s);
        const labelColor = status === "pending" ? "text-muted-2" : "text-ink";
        return (
          <div
            key={s.key}
            className="relative flex flex-col items-center text-center"
          >
            <PipelineNode status={status} index={i + 1} />
            <div className={`mt-3 text-[12px] font-medium ${labelColor}`}>
              {s.short}
            </div>
            <div className="mono mt-1 text-[10px] text-muted">{caption}</div>
          </div>
        );
      })}
    </div>
  );
}
