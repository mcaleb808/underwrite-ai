"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useConfirm, useToast } from "@/components/ui/providers";
import { cancelApplication, deleteApplication } from "@/lib/api";
import type { ApplicationStatus } from "@/lib/types";

const IN_FLIGHT_STATUSES = new Set<string>(["queued", "running", "reeval"]);
const DELETABLE_STATUSES = new Set<string>([
  "awaiting_review",
  "approved",
  "modified",
  "sent",
  "failed",
  "cancelled",
]);

export function AppActions({
  status,
  onCancelRequested,
}: {
  status: ApplicationStatus;
  onCancelRequested: () => void;
}) {
  const router = useRouter();
  const confirm = useConfirm();
  const toast = useToast();
  const [working, setWorking] = useState<"stop" | "delete" | null>(null);

  const isInFlight = IN_FLIGHT_STATUSES.has(status.status);
  const isDeletable = DELETABLE_STATUSES.has(status.status);

  async function handleStop() {
    const ok = await confirm({
      title: "Stop this pipeline?",
      message:
        "The current step will finish, then the run will be cancelled. Any in-flight LLM calls will complete.",
      confirmLabel: "Stop",
      tone: "destructive",
    });
    if (!ok) return;
    setWorking("stop");
    try {
      const result = await cancelApplication(status.task_id);
      onCancelRequested();
      if (result.status === "cancelled") {
        toast.success("Pipeline cancelled.");
      } else {
        toast.info("Stopping the pipeline after the current step.");
      }
    } catch (err) {
      toast.error(`Couldn't stop the pipeline: ${String(err)}`);
    } finally {
      setWorking(null);
    }
  }

  async function handleDelete() {
    const ok = await confirm({
      title: "Remove this application?",
      message: "All its events and the decision will be permanently deleted.",
      confirmLabel: "Remove",
      tone: "destructive",
    });
    if (!ok) return;
    setWorking("delete");
    try {
      await deleteApplication(status.task_id);
      toast.success("Application removed.");
      router.push("/");
    } catch (err) {
      toast.error(`Couldn't remove the application: ${String(err)}`);
      setWorking(null);
    }
  }

  if (!isInFlight && !isDeletable) return null;

  return (
    <div className="flex items-center gap-2">
      {isInFlight ? (
        <button
          type="button"
          onClick={handleStop}
          disabled={working !== null}
          className="btn warn text-[12px]"
          style={{ padding: "6px 12px" }}
        >
          {working === "stop" ? "Stopping…" : "Stop pipeline"}
        </button>
      ) : null}
      {isDeletable ? (
        <button
          type="button"
          onClick={handleDelete}
          disabled={working !== null}
          className="btn bad text-[12px]"
          style={{ padding: "6px 12px" }}
        >
          {working === "delete" ? "Removing…" : "Remove"}
        </button>
      ) : null}
    </div>
  );
}
