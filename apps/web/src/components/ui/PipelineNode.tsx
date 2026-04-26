export type NodeStatus = "done" | "active" | "pending" | "error";

const SIZE = 48;

export function PipelineNode({
  status,
  index,
}: {
  status: NodeStatus;
  index: number;
}) {
  if (status === "active") {
    return (
      <div
        className="relative grid place-items-center"
        style={{ width: SIZE, height: SIZE }}
      >
        <svg
          width={SIZE}
          height={SIZE}
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="ring-spin"
        >
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={SIZE / 2 - 3}
            fill="none"
            stroke="var(--line)"
            strokeWidth={2}
          />
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={SIZE / 2 - 3}
            fill="none"
            stroke="var(--accent)"
            strokeWidth={2}
            strokeDasharray={`${2 * Math.PI * (SIZE / 2 - 3) * 0.3} ${2 * Math.PI * (SIZE / 2 - 3)}`}
            strokeLinecap="round"
          />
        </svg>
        <div
          className="absolute h-3.5 w-3.5 rounded-full"
          style={{ background: "var(--accent)" }}
        />
      </div>
    );
  }

  if (status === "done") {
    return (
      <div
        className="grid place-items-center rounded-full bg-ink text-paper"
        style={{ width: SIZE, height: SIZE }}
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
        >
          <path d="M3.5 8.5l3 3 6-6" />
        </svg>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div
        className="grid place-items-center rounded-full text-paper"
        style={{ width: SIZE, height: SIZE, background: "var(--bad)" }}
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
        >
          <path d="M5 5l6 6M11 5l-6 6" />
        </svg>
      </div>
    );
  }

  return (
    <div
      className="serif grid place-items-center rounded-full text-[14px] text-muted-2"
      style={{
        width: SIZE,
        height: SIZE,
        background: "var(--paper)",
        border: "1.5px dashed var(--line-2)",
      }}
    >
      {index}
    </div>
  );
}
