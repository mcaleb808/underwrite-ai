import Link from "next/link";

import { RecentApplications } from "@/components/RecentApplications";
import { RunButton } from "@/components/RunButton";
import { listPersonas } from "@/lib/api";

export default async function Home() {
  const personas = await listPersonas();

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-16">
      <header className="mb-10 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            UnderwriteAI
          </h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Pick a seed applicant to run the multi-agent underwriting pipeline live,
            or submit your own.
          </p>
        </div>
        <Link
          href="/new"
          className="shrink-0 rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
        >
          + New application
        </Link>
      </header>

      <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        Seed applicants
      </h2>
      <ul className="divide-y divide-zinc-200 rounded-lg border border-zinc-200 bg-white dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-950">
        {personas.map((p) => (
          <li
            key={p.id}
            className="flex items-center justify-between gap-4 px-5 py-4"
          >
            <div className="min-w-0">
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                  {p.name}
                </span>
                <span className="text-xs text-zinc-500 dark:text-zinc-400">
                  {p.age}, {p.district}
                </span>
              </div>
              <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">
                {p.headline}
              </p>
            </div>
            <RunButton personaId={p.id} />
          </li>
        ))}
      </ul>

      <RecentApplications />
    </main>
  );
}
