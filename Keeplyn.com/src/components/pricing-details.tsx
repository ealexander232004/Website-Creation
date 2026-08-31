import { ArrowUpRight, Check, X } from "lucide-react";
import Link from "next/link";
import {
  buildFeatures,
  hostingFeatures,
  type ComparisonFeature,
  websitePlans,
} from "@/lib/plans";

function FeatureStatus({ included }: { included: boolean }) {
  return (
    <span
      className={`mx-auto flex size-10 items-center justify-center rounded-full border ${
        included
          ? "border-[#c9ff3b]/24 bg-[#c9ff3b]/8 text-[#c9ff3b]"
          : "border-[#7568ff]/28 bg-[#7568ff]/8 text-[#8d82ff]"
      }`}
    >
      {included ? (
        <Check className="size-5" strokeWidth={2.5} aria-hidden="true" />
      ) : (
        <X className="size-5" strokeWidth={2.25} aria-hidden="true" />
      )}
      <span className="sr-only">{included ? "Included" : "Not included"}</span>
    </span>
  );
}

function FeatureRows({ features }: { features: ComparisonFeature[] }) {
  return (
    <div>
      {features.map((item) => (
        <div
          key={item.feature}
          className="grid min-h-24 grid-cols-[minmax(0,1fr)_minmax(5.25rem,.7fr)_minmax(5.25rem,.7fr)] border-t border-white/11 sm:grid-cols-[minmax(0,1.55fr)_minmax(7rem,.62fr)_minmax(7rem,.62fr)]"
        >
          <div className="flex items-center px-4 py-5 sm:px-7">
            <p className="max-w-xl text-sm leading-6 text-white/68 sm:text-base">{item.feature}</p>
          </div>
          <div className="flex items-center justify-center border-l border-white/11 bg-white/[0.018] px-2 py-5">
            <FeatureStatus included={item.starter} />
          </div>
          <div className="flex items-center justify-center border-l border-[#7568ff]/20 bg-[#7568ff]/[0.035] px-2 py-5">
            <FeatureStatus included={item.pro} />
          </div>
        </div>
      ))}
    </div>
  );
}

function PlanHeader({ hosting = false }: { hosting?: boolean }) {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_minmax(5.25rem,.7fr)_minmax(5.25rem,.7fr)] sm:grid-cols-[minmax(0,1.55fr)_minmax(7rem,.62fr)_minmax(7rem,.62fr)]">
      <div className="flex items-end px-4 py-6 sm:px-7 sm:py-8">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-white/48 sm:text-[1.875rem] sm:tracking-[0.05em]">Feature</p>
      </div>
      {websitePlans.map((plan) => (
        <div
          id={hosting ? undefined : plan.id}
          key={plan.id}
          className={`scroll-mt-24 border-l px-2 py-6 text-center sm:px-5 sm:py-8 ${
            plan.featured ? "border-[#7568ff]/24 bg-[#7568ff]/[0.045]" : "border-white/11 bg-white/[0.02]"
          }`}
        >
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-white/76 sm:text-sm">{plan.name}</p>
          {hosting ? (
            <div className="mt-2">
              <p className="text-lg font-semibold tracking-[-0.05em] text-white sm:text-3xl">
                {plan.hosting.replace("/mo", "")}
              </p>
              <p className="mt-0.5 text-[9px] font-medium uppercase tracking-[0.12em] text-white/42">Per month</p>
            </div>
          ) : (
            <p className="mt-2 text-lg font-semibold tracking-[-0.05em] text-white sm:text-3xl">{plan.price}</p>
          )}
        </div>
      ))}
    </div>
  );
}

export function PricingDetails() {
  return (
    <section className="relative overflow-hidden bg-[#050505] pb-24 text-white sm:pb-32">
      <div
        className="pointer-events-none absolute left-1/2 top-72 h-[42rem] w-[42rem] -translate-x-1/2 rounded-full bg-[#7568ff]/7 blur-[150px]"
        aria-hidden="true"
      />
      <div className="site-container relative">
        <div className="overflow-hidden border border-white/14 bg-[#08080c]/88 shadow-[0_45px_160px_rgba(0,0,0,0.42)]">
          <PlanHeader />
          <FeatureRows features={buildFeatures} />

          <div className="grid grid-cols-[minmax(0,1fr)_minmax(5.25rem,.7fr)_minmax(5.25rem,.7fr)] border-t border-white/11 sm:grid-cols-[minmax(0,1.55fr)_minmax(7rem,.62fr)_minmax(7rem,.62fr)]">
            <div className="flex items-center px-4 py-6 sm:px-7">
              <p className="text-xs uppercase tracking-[0.14em] text-white/32">Ready when you are</p>
            </div>
            {websitePlans.map((plan) => (
              <div
                key={plan.id}
                className={`border-l p-2 sm:p-4 ${plan.featured ? "border-[#7568ff]/24 bg-[#7568ff]/[0.045]" : "border-white/11 bg-white/[0.02]"}`}
              >
                <Link
                  href={`/start?plan=${plan.id}`}
                  className="group flex min-h-16 items-center justify-center gap-2 border border-white/14 px-2 text-center text-xs font-semibold transition-colors hover:border-[#c9ff3b] hover:text-[#c9ff3b] sm:text-sm"
                >
                  Choose {plan.name}
                  <ArrowUpRight className="hidden size-3.5 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 sm:block" aria-hidden="true" />
                </Link>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-24 sm:mt-32">
          <div className="mb-10 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#c9ff3b]">Optional service</p>
              <h2 className="mt-4 max-w-4xl text-[clamp(3.5rem,8vw,7.5rem)] font-semibold leading-[0.82] tracking-[-0.085em]">
                Hosting &amp; updates.
              </h2>
            </div>
            <p className="max-w-sm text-sm leading-6 text-white/44">
              Keep your site fast, current, and completely hands-off.
            </p>
          </div>

          <div className="overflow-hidden border border-white/14 bg-[#08080c]/88">
            <PlanHeader hosting />
            <FeatureRows features={hostingFeatures} />
          </div>
        </div>
      </div>
    </section>
  );
}
