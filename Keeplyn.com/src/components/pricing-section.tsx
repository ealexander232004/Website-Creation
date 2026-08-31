import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { websitePlans } from "@/lib/plans";

export function PricingSection() {
  return (
    <section id="pricing" className="relative overflow-hidden border-y border-white/10 bg-[#07070a]/90 py-24 text-white backdrop-blur-sm sm:py-32">
      <div className="site-container">
        <div className="flex flex-col justify-between gap-7 sm:flex-row sm:items-end">
          <h2 className="text-[clamp(4.5rem,10vw,9rem)] font-semibold leading-[0.78] tracking-[-0.09em]">
            Choose a build.
          </h2>
          <Link href="/pricing" className="group flex w-fit items-center gap-2 text-sm text-white/48 hover:text-[#c9ff3b]">
            See every detail
            <ArrowUpRight className="size-4 transition-transform group-hover:-translate-y-1 group-hover:translate-x-1" aria-hidden="true" />
          </Link>
        </div>

        <div className="mt-14 grid overflow-hidden border border-white/14 bg-white/10 md:grid-cols-2 md:gap-px">
          {websitePlans.map((plan) => (
            <Link
              key={plan.id}
              href={`/pricing#${plan.id}`}
              className={`group relative flex min-h-[32rem] flex-col justify-between bg-[#08080b] p-7 transition-colors duration-500 hover:bg-[#111019] sm:p-10 ${
                plan.featured ? "border-t border-[#c9ff3b] md:border-t-0 md:border-l" : ""
              }`}
            >
              {plan.featured ? <div className="absolute inset-x-0 top-0 h-px bg-[#c9ff3b] shadow-[0_0_30px_rgba(201,255,59,.7)]" /> : null}
              <div>
                <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-white/35">Website build</p>
                <h3 className="mt-5 text-5xl font-semibold tracking-[-0.075em] sm:text-6xl">{plan.name}</h3>
                <p className="mt-4 max-w-sm text-sm leading-6 text-white/44">{plan.summary}</p>
              </div>

              <div>
                <p className="text-[clamp(3.5rem,7vw,6.5rem)] font-semibold leading-none tracking-[-0.085em]">{plan.price}</p>
                <p className="mt-3 text-sm text-[#c9ff3b]">+ {plan.hosting} for hosting &amp; updates</p>
                <ul className="mt-8 flex flex-wrap gap-2" aria-label={`${plan.name} highlights`}>
                  {plan.homeFeatures.map((feature) => (
                    <li key={feature} className="border border-white/12 px-3 py-2 text-[10px] text-white/58">{feature}</li>
                  ))}
                </ul>
                <span className="mt-9 flex items-center justify-between border-t border-white/14 pt-5 text-sm font-medium group-hover:text-[#c9ff3b]">
                  View {plan.name}
                  <ArrowUpRight className="size-4 transition-transform group-hover:-translate-y-1 group-hover:translate-x-1" aria-hidden="true" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
