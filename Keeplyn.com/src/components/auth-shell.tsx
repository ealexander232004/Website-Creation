import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { BrandLogo } from "./brand-logo";

/** Minimal full-screen frame for account pages outside the request flow. */
export function AuthShell({
  kicker,
  title,
  description,
  children,
}: {
  kicker: string;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <main className="relative min-h-svh overflow-hidden bg-[#050505] text-white">
      <div className="pointer-events-none absolute left-1/2 top-1/3 size-[42rem] -translate-x-1/2 rounded-full bg-[#7568ff]/10 blur-[170px]" aria-hidden="true" />
      <header className="relative border-b border-white/10">
        <div className="site-container flex h-[68px] items-center justify-between">
          <BrandLogo />
          <Link href="/start?mode=signin" className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.1em] text-white/42 transition-colors hover:text-white">
            <ArrowLeft className="size-3.5" aria-hidden="true" />
            Sign in
          </Link>
        </div>
      </header>
      <section className="site-container relative py-16 sm:py-24">
        <div className="max-w-2xl">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9ff3b]">{kicker}</p>
          <h1 className="mt-4 text-[clamp(3rem,7vw,6rem)] font-semibold leading-[0.84] tracking-[-0.075em]">{title}</h1>
          <p className="mt-6 max-w-xl text-sm leading-7 text-white/48 sm:text-base">{description}</p>
          <div className="mt-10">{children}</div>
        </div>
      </section>
    </main>
  );
}

export const authFieldClass =
  "mt-2 w-full border border-white/14 bg-white/[0.045] px-4 py-3.5 text-[15px] text-white outline-none transition placeholder:text-white/24 focus:border-[#c9ff3b]/70 focus:bg-white/[0.07]";
