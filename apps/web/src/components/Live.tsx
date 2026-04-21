"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { AppActions } from "@/components/AppActions";
import { DecisionCard } from "@/components/DecisionCard";
import { FailureCard } from "@/components/FailureCard";
import { MedicalDocs } from "@/components/MedicalDocs";
import { ReviewActions } from "@/components/ReviewActions";
import { RiskFactors } from "@/components/RiskFactors";
import { Timeline } from "@/components/Timeline";
import { UsagePill, type Usage } from "@/components/UsagePill";
import { eventsUrl, getApplication } from "@/lib/api";
import type { ApplicationStatus, LiveEvent } from "@/lib/types";

function readUsage(event: LiveEvent): Usage | null {
  if (event.node !== "orchestrator" || event.type !== "usage") return null;
  return {
    prompt_tokens: Number(event.prompt_tokens ?? 0),
    completion_tokens: Number(event.completion_tokens ?? 0),
    total_tokens: Number(event.total_tokens ?? 0),
    cost_usd: Number(event.cost_usd ?? 0),
    calls: Number(event.calls ?? 0),
  };
}

export function Live({ initial }: { initial: ApplicationStatus }) {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [status, setStatus] = useState<ApplicationStatus>(initial);
  const [usage, setUsage] = useState<Usage | undefined>(undefined);
  const [finished, setFinished] = useState(false);
  const [startedAt] = useState(() => Date.now());
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const source = new EventSource(eventsUrl(initial.task_id));
    sourceRef.current = source;

    source.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data) as LiveEvent;
        const updatedUsage = readUsage(event);
        if (updatedUsage) {
          setUsage(updatedUsage);
        } else {
          setEvents((prev) => [...prev, event]);
        }
        if (event.type === "closed" || event.type === "finalized" || event.type === "error") {
          setFinished(true);
          // refresh status to pull the final decision
          getApplication(initial.task_id).then(setStatus).catch(() => {});
        }
      } catch {
        // ignore malformed events
      }
    };

    source.onerror = () => {
      source.close();
    };

    return () => {
      source.close();
      sourceRef.current = null;
    };
  }, [initial.task_id]);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
            {initial.reference_number}
          </h1>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            status: {status.status}
            {status.risk_score !== null
              ? ` · risk score ${status.risk_score} (${status.risk_band})`
              : ""}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <UsagePill usage={usage} startedAt={startedAt} finished={finished} />
          <AppActions
            status={status}
            onCancelRequested={() => {
              getApplication(initial.task_id).then(setStatus).catch(() => {});
            }}
          />
          <Link
            href="/"
            className="text-xs text-zinc-500 underline-offset-2 hover:underline dark:text-zinc-400"
          >
            ← back
          </Link>
        </div>
      </header>

      <section>
        <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          Pipeline
        </h2>
        <Timeline events={events} />
      </section>

      {status.risk_factors.length > 0 ? <RiskFactors factors={status.risk_factors} /> : null}

      <MedicalDocs taskId={initial.task_id} />

      {status.decision ? (
        <>
          <DecisionCard decision={status.decision} />
          <ReviewActions status={status} onChange={setStatus} />
        </>
      ) : status.status === "failed" ? (
        <FailureCard taskId={initial.task_id} />
      ) : null}
    </div>
  );
}
