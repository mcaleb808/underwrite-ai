import Link from "next/link";

import { RecentApplications } from "@/components/RecentApplications";
import { RunButton } from "@/components/RunButton";
import { listPersonas } from "@/lib/api";

function initials(name: string): string {
  return name
    .split(" ")
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export default async function Home() {
  const personas = await listPersonas();

  return (
    <main className="flex-1">
      <section className="border-b border-line px-6 py-16 sm:px-10 sm:py-20">
        <div className="mx-auto w-full max-w-[1240px]">
          <div className="max-w-[720px]">
            <h1 className="serif m-0 text-[44px] leading-[1.05] tracking-[-0.02em] sm:text-[64px] sm:leading-[1.0]">
              Health insurance,
              <br />
              <em className="text-accent">underwritten in seconds.</em>
            </h1>
            <p className="mt-6 max-w-[520px] text-[16px] leading-[1.55] text-muted sm:text-[17px]">
              Five specialised agents read documents, score risk, and produce an
              auditable decision - with a senior underwriter still in the loop.
            </p>
            <div className="mt-8">
              <Link href="/new" className="btn">
                + New application
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="px-6 pb-6 pt-12 sm:px-10 sm:pb-8 sm:pt-16">
        <div className="mx-auto w-full max-w-[1240px]">
          <div className="mb-5 flex items-baseline justify-between">
            <h2 className="serif m-0 text-[28px] tracking-[-0.01em]">
              Seed applicants
            </h2>
            <span className="text-[12px] text-muted">Try a sample case</span>
          </div>

          <ul className="overflow-hidden rounded border border-line bg-paper">
            {personas.map((p, i) => (
              <li
                key={p.id}
                className={`flex items-center gap-4 px-5 py-5 sm:px-6 ${
                  i < personas.length - 1 ? "border-b border-line" : ""
                }`}
              >
                <div
                  aria-hidden
                  className="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-line-2 text-[13px] font-medium text-ink-2"
                  style={{
                    background:
                      "color-mix(in oklch, var(--accent) 14%, var(--paper-2))",
                  }}
                >
                  {initials(p.name)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
                    <span className="serif text-[20px]">{p.name}</span>
                    <span className="text-[12px] text-muted">
                      {p.age} · {p.district}
                    </span>
                  </div>
                  <p className="mt-0.5 truncate text-[13px] text-muted">
                    {p.headline}
                  </p>
                </div>
                <RunButton personaId={p.id} />
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="px-6 pb-16 pt-6 sm:px-10 sm:pb-20">
        <div className="mx-auto w-full max-w-[1240px]">
          <RecentApplications />
        </div>
      </section>
    </main>
  );
}
