import Link from "next/link";

import { Logo } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";

export function TopNav() {
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-line bg-paper px-6 py-4 sm:px-10 sm:py-5">
      <div className="flex items-center gap-9">
        <Link href="/" className="text-ink">
          <Logo />
        </Link>
        <nav className="flex gap-6 text-[13px]">
          <Link
            href="/"
            className="border-b border-ink pb-1 font-medium text-ink"
          >
            Cases
          </Link>
        </nav>
      </div>
      <ThemeToggle />
    </header>
  );
}
