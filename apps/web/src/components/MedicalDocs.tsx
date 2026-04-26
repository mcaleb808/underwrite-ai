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
    <div className="rounded border border-line bg-paper px-5 py-4">
      <div className="field-label mb-3">Medical documents</div>
      <ul className="m-0 list-none space-y-2 p-0 text-[13px]">
        {files.map((name) => (
          <li key={name}>
            <a
              href={fileUrl(taskId, name)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2.5 text-ink hover:text-accent"
            >
              <svg width="12" height="14" viewBox="0 0 12 14" fill="none" stroke="currentColor" strokeWidth="1.4">
                <path d="M2 1h6l3 3v9H2z" />
                <path d="M8 1v3h3" />
              </svg>
              <span className="truncate">{name}</span>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
