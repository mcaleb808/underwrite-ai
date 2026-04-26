"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppActions } from "@/components/AppActions";
import { DecisionCard } from "@/components/DecisionCard";
import { EmailReceipt } from "@/components/EmailReceipt";
import { EventStream } from "@/components/EventStream";
import { FailureCard } from "@/components/FailureCard";
import { MedicalDocs } from "@/components/MedicalDocs";
import { ReviewActions, type ApproveResult } from "@/components/ReviewActions";
import { RiskFactors } from "@/components/RiskFactors";
import { Timeline } from "@/components/Timeline";
import { UsagePill, type Usage } from "@/components/UsagePill";
import { PipelineStrip } from "@/components/ui/PipelineStrip";
import { RiskArc } from "@/components/ui/RiskArc";
import { useToast } from "@/components/ui/providers";
import { eventsUrl, getApplication, reevaluate } from "@/lib/api";
import { buildStepStates } from "@/lib/pipeline";
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

function elapsedLabel(ms: number): string {
  const s = ms / 1000;
  if (s < 60) return `${s.toFixed(1)}s`;
  const m = Math.floor(s / 60);
  return `${m}m ${Math.floor(s % 60)}s`;
}

export function Live({ initial }: { initial: ApplicationStatus }) {
  const toast = useToast();
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [status, setStatus] = useState<ApplicationStatus>(initial);
  const [usage, setUsage] = useState<Usage | undefined>(undefined);
  const [finished, setFinished] = useState(false);
  const [startedAt, setStartedAt] = useState(() => Date.now());
  const [now, setNow] = useState(() => Date.now());
  const [approveResult, setApproveResult] = useState<ApproveResult | null>(null);
  const [runEpoch, setRunEpoch] = useState(0);

  const refreshStatus = useCallback(
    async (signal?: AbortSignal) => {
      try {
        const next = await getApplication(initial.task_id);
        if (signal?.aborted) return;
        setStatus(next);
      } catch (err) {
        if (signal?.aborted) return;
        toast.error(
          `Couldn't refresh case state: ${err instanceof Error ? err.message : String(err)}`,
        );
      }
    },
    [initial.task_id, toast],
  );

  useEffect(() => {
    const source = new EventSource(eventsUrl(initial.task_id));
    const controller = new AbortController();

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
          void refreshStatus(controller.signal);
        }
      } catch {
        // ignore malformed events
      }
    };

    source.onerror = () => {
      source.close();
    };

    return () => {
      controller.abort();
      source.close();
    };
  }, [initial.task_id, runEpoch, refreshStatus]);

  useEffect(() => {
    if (finished) return;
    const id = window.setInterval(() => setNow(Date.now()), 200);
    return () => window.clearInterval(id);
  }, [finished]);

  const handleReevaluate = useCallback(async () => {
    await reevaluate(initial.task_id);
    setEvents([]);
    setUsage(undefined);
    setFinished(false);
    setStartedAt(Date.now());
    setNow(Date.now());
    setApproveResult(null);
    setStatus((prev) => ({
      ...prev,
      status: "reeval",
      decision: null,
      email_status: null,
      risk_score: null,
      risk_band: null,
      risk_factors: [],
    }));
    setRunEpoch((e) => e + 1);
  }, [initial.task_id]);

  const { steps, finalized, failed } = useMemo(
    () => buildStepStates(events),
    [events],
  );

  const isRunning = !finished && !failed && !finalized;
  const elapsed = now - startedAt;

  const headerPill = isRunning ? (
    <span className="chip accent">
      <span className="pulse-dot" style={{ width: 6, height: 6 }} />
      Pipeline running · {elapsedLabel(elapsed)}
    </span>
  ) : failed || status.status === "failed" ? (
    <span
      className="chip"
      style={{ background: "var(--bad)", color: "white", borderColor: "var(--bad)" }}
    >
      Pipeline failed
    </span>
  ) : status.status === "cancelled" ? (
    <span className="chip">Cancelled</span>
  ) : (
    <span
      className="chip"
      style={{ background: "var(--good)", color: "white", borderColor: "var(--good)" }}
    >
      ✓ Pipeline finished
    </span>
  );

  return (
    <main className="flex-1">
      <section className="border-b border-line px-6 py-8 sm:px-10 sm:py-10">
        <div className="mx-auto w-full max-w-[1240px]">
          <Link href="/" className="text-[12px] text-muted hover:text-ink">
            ← All cases
          </Link>
          <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="serif m-0 text-[36px] leading-none tracking-[-0.02em] sm:text-[44px]">
                {status.reference_number}
              </h1>
              <div className="mono mt-2 text-[13px] text-muted">
                status: {status.status}
                {status.risk_score !== null && status.risk_band ? (
                  <>
                    {" · "}risk {status.risk_score.toFixed(1)} ({status.risk_band})
                  </>
                ) : null}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              {headerPill}
              <AppActions
                status={status}
                onCancelRequested={() => {
                  void refreshStatus();
                }}
              />
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto w-full max-w-[1240px] px-6 py-10 sm:px-10 sm:py-12">
        <div className="grid gap-10 lg:grid-cols-[1fr_360px]">
          <div className="min-w-0 space-y-10">
            <section>
              <SectionHead title="Pipeline" />
              <div className="mt-6">
                <PipelineStrip steps={steps} />
              </div>
              <div className="mt-8">
                <Timeline steps={steps} finalized={finalized} failed={failed} />
              </div>
              <div className="mt-5">
                <EventStream events={events} />
              </div>
            </section>

            {status.decision ? (
              <section>
                <SectionHead title="Decision" />
                <div className="mt-4">
                  <DecisionCard decision={status.decision} />
                  <ReviewActions
                    status={status}
                    onChange={setStatus}
                    onApproved={setApproveResult}
                    onReevaluate={handleReevaluate}
                  />
                </div>
                {(approveResult || status.email_status) ? (
                  <EmailReceipt
                    status={status}
                    emailStatus={approveResult?.email_status ?? status.email_status ?? "sent"}
                    providerMessageId={approveResult?.provider_message_id ?? null}
                  />
                ) : null}
              </section>
            ) : status.status === "failed" ? (
              <FailureCard taskId={initial.task_id} />
            ) : null}
          </div>

          <aside className="space-y-7">
            {!isRunning && status.risk_score !== null ? (
              <RiskArc score={status.risk_score} band={status.risk_band} />
            ) : (
              <div className="rounded border border-line bg-paper px-5 py-6 text-center text-[12px] text-muted">
                {isRunning
                  ? "Risk score will appear once the assessor finishes."
                  : "Risk score will appear once the assessor runs."}
              </div>
            )}

            {!isRunning && status.risk_factors.length > 0 ? (
              <div className="rounded border border-line bg-paper px-5 py-5">
                <RiskFactors factors={status.risk_factors} />
              </div>
            ) : null}

            <MedicalDocs taskId={initial.task_id} />

            <UsagePill usage={usage} startedAt={startedAt} finished={finished} />
          </aside>
        </div>
      </div>
    </main>
  );
}

function SectionHead({ title }: { title: string }) {
  return (
    <div className="flex items-baseline gap-3">
      <h2 className="serif m-0 text-[24px] tracking-[-0.01em]">{title}</h2>
      <div className="hr flex-1" />
    </div>
  );
}
