import { RunButton } from "@/components/RunButton";
import { listPersonas } from "@/lib/api";

export default async function Home() {
  const personas = await listPersonas();

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-16">
      <header className="mb-10">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          UnderwriteAI
        </h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Pick a seed applicant to run the multi-agent underwriting pipeline live.
        </p>
      </header>

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
    </main>
  );
}
