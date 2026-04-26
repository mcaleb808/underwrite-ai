import Link from "next/link";

import { ApplicantForm } from "@/components/ApplicantForm";
import { listDistricts } from "@/lib/api";

export default async function NewApplicationPage() {
  const districts = await listDistricts();

  return (
    <main className="mx-auto w-full max-w-[760px] flex-1 px-6 py-12 sm:px-10 sm:py-16">
      <Link href="/" className="text-[12px] text-muted hover:text-ink">
        ← All cases
      </Link>
      <h1 className="serif mt-3 text-[40px] leading-[1.0] tracking-[-0.02em] sm:text-[52px]">
        Tell us about
        <br />
        the applicant.
      </h1>
      <p className="mt-3 max-w-[480px] text-[14px] leading-[1.55] text-muted">
        Required fields are marked. Underwriter-only details are tucked behind a
        toggle below.
      </p>

      <div className="mt-12">
        <ApplicantForm districts={districts} />
      </div>
    </main>
  );
}
