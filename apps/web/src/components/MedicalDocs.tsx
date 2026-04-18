"use client";

import { useEffect, useState } from "react";

import { fileUrl, listFiles } from "@/lib/api";

export function MedicalDocs({ taskId }: { taskId: string }) {
  const [files, setFiles] = useState<string[]>([]);

  useEffect(() => {
    listFiles(taskId).then(setFiles).catch(() => setFiles([]));
  }, [taskId]);

  if (files.length === 0) return null;

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        Medical documents
      </h2>
      <ul className="space-y-1.5 text-sm">
        {files.map((name) => (
          <li key={name}>
            <a
              href={fileUrl(taskId, name)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-zinc-700 underline-offset-2 hover:underline dark:text-zinc-300"
            >
              <span className="text-zinc-400">PDF</span>
              {name}
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
