import type { ReactNode } from "react";
import Link from "next/link";
import { SiteFooter } from "./home-sections";
import { SiteHeader } from "./site-header";

const policyLinks = [
  { label: "Terms of Service", href: "/terms-of-service" },
  { label: "Privacy Policy", href: "/privacy-policy" },
  {
    label: "Billing & Cancellation",
    href: "/billing-cancellation-policy",
  },
];

type PolicyPageProps = {
  children: ReactNode;
  currentPath: string;
  summary: string;
  title: string;
};

type PolicySectionProps = {
  children: ReactNode;
  number: string;
  title: string;
};

export function PolicyPage({
  children,
  currentPath,
  summary,
  title,
}: PolicyPageProps) {
  return (
    <>
      <SiteHeader />
      <main className="relative isolate overflow-hidden bg-[#050505] text-white">
        <div
          className="pointer-events-none absolute top-0 right-[-18rem] size-[40rem] rounded-full bg-[#7568ff]/10 blur-[130px]"
          aria-hidden="true"
        />
        <div
          className="pointer-events-none absolute top-[35rem] left-[-16rem] size-[34rem] rounded-full bg-[#c9ff3b]/5 blur-[130px]"
          aria-hidden="true"
        />

        <article className="site-container relative py-20 sm:py-28 lg:py-32">
          <header className="grid gap-10 border-b border-white/12 pb-16 lg:grid-cols-[1.45fr_0.55fr] lg:items-end lg:gap-20 lg:pb-20">
            <div>
              <p className="mb-7 text-[10px] font-semibold uppercase tracking-[0.2em] text-mint">
                Keeplyn / Policies
              </p>
              <h1 className="max-w-5xl text-[clamp(4.25rem,10vw,9rem)] font-semibold leading-[0.78] tracking-[-0.085em]">
                {title}
              </h1>
            </div>
            <div className="max-w-lg lg:pb-1">
              <p className="text-base leading-7 text-white/58">{summary}</p>
              <p className="mt-6 text-[10px] font-medium uppercase tracking-[0.16em] text-white/30">
                Effective August 31, 2026
              </p>
            </div>
          </header>

          <div className="grid gap-16 pt-14 lg:grid-cols-[14rem_minmax(0,46rem)] lg:justify-between lg:gap-24 lg:pt-20">
            <aside className="lg:sticky lg:top-24 lg:self-start">
              <p className="mb-5 text-[9px] font-semibold uppercase tracking-[0.2em] text-white/28">
                Policy index
              </p>
              <nav className="flex flex-col border-t border-white/12" aria-label="Policy pages">
                {policyLinks.map((link) => {
                  const isCurrent = link.href === currentPath;

                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      aria-current={isCurrent ? "page" : undefined}
                      className={`border-b border-white/12 py-4 text-sm transition-colors ${
                        isCurrent
                          ? "font-semibold text-mint"
                          : "text-white/45 hover:text-white"
                      }`}
                    >
                      {link.label}
                    </Link>
                  );
                })}
              </nav>
            </aside>

            <div>{children}</div>
          </div>
        </article>
      </main>
      <SiteFooter />
    </>
  );
}

export function PolicySection({ children, number, title }: PolicySectionProps) {
  return (
    <section className="grid gap-5 border-b border-white/12 py-10 first:pt-0 sm:grid-cols-[3.25rem_minmax(0,1fr)] sm:gap-7 sm:py-12">
      <p className="font-mono text-xs text-white/24" aria-hidden="true">
        {number}
      </p>
      <div>
        <h2 className="text-2xl font-semibold tracking-[-0.035em] text-white sm:text-3xl">
          {title}
        </h2>
        <div className="mt-5 space-y-4 text-[0.95rem] leading-7 text-white/58 [&_a]:font-medium [&_a]:text-white [&_a]:underline [&_a]:decoration-white/30 [&_a]:underline-offset-4 [&_a]:transition-colors hover:[&_a]:text-mint [&_li]:pl-2 [&_strong]:font-semibold [&_strong]:text-white/78 [&_ul]:ml-5 [&_ul]:list-disc [&_ul]:space-y-2">
          {children}
        </div>
      </div>
    </section>
  );
}
