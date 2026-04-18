"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { DecisionCard } from "@/components/DecisionCard";
import { MedicalDocs } from "@/components/MedicalDocs";
import { ReviewActions } from "@/components/ReviewActions";
import { RiskFactors } from "@/components/RiskFactors";
import { Timeline } from "@/components/Timeline";
import { eventsUrl, getApplication } from "@/lib/api";
import type { ApplicationStatus, LiveEvent } from "@/lib/types";

export function Live({ initial }: { initial: ApplicationStatus }) {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [status, setStatus] = useState<ApplicationStatus>(initial);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const source = new EventSource(eventsUrl(initial.task_id));
    sourceRef.current = source;

    source.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data) as LiveEvent;
        setEvents((prev) => [...prev, event]);
        if (event.type === "closed" || event.type === "finalized") {
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
      <header className="flex items-baseline justify-between">
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
        <Link
          href="/"
          className="text-xs text-zinc-500 underline-offset-2 hover:underline dark:text-zinc-400"
        >
          ← back
        </Link>
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
      ) : null}
    </div>
  );
}
