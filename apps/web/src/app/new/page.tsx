import Link from "next/link";

import { ApplicantForm } from "@/components/ApplicantForm";
import { listDistricts } from "@/lib/api";

export default async function NewApplicationPage() {
  const districts = await listDistricts();

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-12">
      <header className="mb-8 flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            New application
          </h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Enter applicant details and (optionally) upload medical PDFs. The
            multi-agent pipeline will run live and you can approve, modify, or
            re-evaluate the verdict.
          </p>
        </div>
        <Link
          href="/"
          className="text-xs text-zinc-500 underline-offset-2 hover:underline dark:text-zinc-400"
        >
          ← back
        </Link>
      </header>

      <ApplicantForm districts={districts} />
    </main>
  );
}
