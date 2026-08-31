import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { websitePlans } from "@/lib/plans";

export function PricingSection() {
  return (
    <section id="pricing" className="relative isolate min-h-[105svh] overflow-hidden py-24 text-white sm:py-32 lg:py-40">
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-48 bg-gradient-to-b from-transparent via-[#050505]/12 to-transparent"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute left-1/2 top-[28%] h-[66%] w-[min(88%,68rem)] -translate-x-1/2 bg-[radial-gradient(ellipse_at_center,rgba(5,5,7,0.84)_0%,rgba(5,5,7,0.5)_48%,transparent_76%)]"
        aria-hidden="true"
      />
      <div className="site-container relative z-10">
        <div>
          <h2 className="max-w-5xl text-[clamp(4.5rem,10vw,9rem)] font-semibold leading-[0.78] tracking-[-0.09em]">
            Choose your build.
          </h2>
        </div>

        <div className="mx-auto mt-16 grid max-w-5xl gap-4 md:grid-cols-2 lg:mt-20">
          {websitePlans.map((plan) => (
            <div key={plan.id} className="group flex flex-col">
              <article
                className={`relative isolate flex min-h-[27rem] flex-1 flex-col justify-between overflow-hidden border p-7 shadow-[0_30px_100px_rgba(0,0,0,0.38)] transition duration-500 group-hover:-translate-y-1 sm:p-9 ${
                  plan.featured
                    ? "border-white/16 bg-[linear-gradient(145deg,rgba(11,12,13,0.94),rgba(6,6,8,0.9))] group-hover:border-white/38 md:bg-[linear-gradient(145deg,rgba(13,14,15,0.74),rgba(7,7,10,0.52))]"
                    : "border-white/16 bg-[linear-gradient(145deg,rgba(10,10,14,0.94),rgba(5,5,7,0.9))] group-hover:border-white/38 md:bg-[linear-gradient(145deg,rgba(12,12,17,0.72),rgba(5,5,7,0.48))]"
                }`}
              >
                <div
                  className={`pointer-events-none absolute -right-24 -top-24 size-64 rounded-full blur-3xl transition-opacity duration-500 group-hover:opacity-100 ${
                    plan.featured ? "bg-[#c9ff3b]/8 opacity-70" : "bg-[#7568ff]/10 opacity-60"
                  }`}
                  aria-hidden="true"
                />
                <div className="relative z-10">
                  <h3 className="text-5xl font-semibold tracking-[-0.075em] sm:text-6xl">{plan.name}</h3>
                  <p className="mt-5 max-w-sm text-sm leading-6 text-white/48">{plan.summary}</p>
                </div>

                <div className="relative z-10 mt-16">
                  <p className="text-[clamp(3.75rem,7vw,6rem)] font-semibold leading-none tracking-[-0.085em]">{plan.price}</p>
                  <p className="mt-3 text-sm text-[#c9ff3b]">+ an optional {plan.hosting} for hosting &amp; updates</p>
                </div>
              </article>
            </div>
          ))}
        </div>
        <Link
          href="/pricing"
          className="group relative mx-auto mt-4 flex max-w-5xl items-center justify-center border border-[#c9ff3b]/65 bg-[#c9ff3b] px-6 py-4 text-center text-sm font-medium text-black transition-colors hover:bg-[#d5ff69]"
        >
          See what&apos;s included
          <ArrowUpRight className="absolute right-6 size-4 transition-transform group-hover:-translate-y-1 group-hover:translate-x-1" aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}
