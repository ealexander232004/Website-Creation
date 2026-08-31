import { ArrowUpRight } from "lucide-react";
import Link from "next/link";

const plans = [
  { kind: "Build", name: "Starter", price: "$750", cadence: "once", features: ["4 pages", "Responsive", "SEO setup"] },
  { kind: "Build", name: "Pro", price: "$1,500", cadence: "once", features: ["8 pages", "CMS", "Integrations"], featured: true },
  { kind: "Care", name: "Starter", price: "$49.99", cadence: "/ month", features: ["Hosting", "Backups", "30m edits"] },
  { kind: "Care", name: "Pro", price: "$99.99", cadence: "/ month", features: ["Priority", "90m edits", "Performance"], featured: true },
];

export function PricingSection() {
  return (
    <section id="pricing" className="overflow-hidden border-y border-white/10 bg-[#08080b] py-24 text-white sm:py-32">
      <div className="site-container">
        <div className="flex flex-col justify-between gap-8 sm:flex-row sm:items-end">
          <h2 className="text-[clamp(4.5rem,10vw,9rem)] font-semibold leading-[0.78] tracking-[-0.09em]">
            Pick a level.
          </h2>
          <p className="max-w-[12rem] text-sm leading-6 text-white/45">Build once. Add care when you want it.</p>
        </div>

        <div className="mt-16 grid gap-px overflow-hidden border border-white/10 bg-white/10 sm:grid-cols-2 xl:grid-cols-4">
          {plans.map((plan) => (
            <article
              key={`${plan.kind}-${plan.name}`}
              className={`group relative flex min-h-[26rem] flex-col justify-between p-7 transition-colors duration-500 sm:p-8 ${
                plan.featured ? "bg-[#111019] hover:bg-[#17142b]" : "bg-[#08080b] hover:bg-[#0d0d12]"
              }`}
            >
              {plan.featured && <div className="absolute inset-x-0 top-0 h-px bg-[#c9ff3b] shadow-[0_0_24px_#c9ff3b]" />}
              <div>
                <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-white/38">{plan.kind}</p>
                <h3 className="mt-4 text-3xl font-semibold tracking-[-0.06em]">{plan.name}</h3>
              </div>

              <div>
                <p className="text-[clamp(2.5rem,4vw,4.5rem)] font-semibold leading-none tracking-[-0.075em]">{plan.price}</p>
                <p className="mt-2 text-xs text-white/35">{plan.cadence}</p>
                <ul className="mt-8 flex flex-wrap gap-2" aria-label={`${plan.kind} ${plan.name} includes`}>
                  {plan.features.map((feature) => (
                    <li key={feature} className="border border-white/12 px-3 py-2 text-[10px] text-white/55">{feature}</li>
                  ))}
                </ul>
                <Link href="/contact" className="mt-8 flex items-center justify-between border-t border-white/14 pt-5 text-sm font-medium hover:text-[#c9ff3b]">
                  Choose
                  <ArrowUpRight className="size-4 transition-transform group-hover:-translate-y-1 group-hover:translate-x-1" aria-hidden="true" />
                </Link>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
