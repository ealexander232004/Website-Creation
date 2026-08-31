import { ArrowUpRight, Check } from "lucide-react";
import Link from "next/link";

interface Plan {
  name: string;
  price: string;
  cadence: string;
  description: string;
  features: string[];
  featured?: boolean;
}

const builds: Plan[] = [
  {
    name: "Starter",
    price: "$750",
    cadence: "one time",
    description: "A focused site for one clear service, offer, or local business.",
    features: ["Up to 4 pages", "Responsive design", "Contact setup", "Foundational SEO"],
  },
  {
    name: "Pro",
    price: "$1,500",
    cadence: "one time",
    description: "A deeper system for a growing business with more to say and sell.",
    features: ["Up to 8 pages", "Messaging guidance", "CMS or blog", "Analytics + integrations"],
    featured: true,
  },
];

const care: Plan[] = [
  {
    name: "Starter Care",
    price: "$49.99",
    cadence: "per month",
    description: "The essentials to keep the site secure, current, and online.",
    features: ["Managed hosting", "SSL + backups", "Core updates", "30 minutes of edits"],
  },
  {
    name: "Pro Care",
    price: "$99.99",
    cadence: "per month",
    description: "More hands-on support for a site that keeps evolving.",
    features: ["Everything in Starter", "90 minutes of edits", "Priority support", "Performance review"],
    featured: true,
  },
];

function PlanCard({ plan, index }: { plan: Plan; index: number }) {
  return (
    <article
      className={`relative flex h-full flex-col border p-6 transition-transform duration-500 hover:-translate-y-2 sm:p-8 ${
        plan.featured
          ? "border-navy bg-navy text-white shadow-[10px_10px_0_#3155ff]"
          : "border-navy/20 bg-white text-navy shadow-[8px_8px_0_rgba(21,21,21,0.07)]"
      }`}
      data-reveal
      style={{ transitionDelay: `${index * 80}ms` }}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className={`font-mono text-[9px] uppercase tracking-[0.16em] ${plan.featured ? "text-mint" : "text-violet"}`}>
            {plan.featured ? "Most chosen" : "Straightforward"}
          </p>
          <h3 className="mt-4 text-2xl font-semibold tracking-[-0.045em]">{plan.name}</h3>
        </div>
        <span className={`font-mono text-[10px] ${plan.featured ? "text-white/35" : "text-slate"}`}>0{index + 1}</span>
      </div>

      <p className={`mt-5 min-h-14 text-sm leading-6 ${plan.featured ? "text-white/55" : "text-slate"}`}>
        {plan.description}
      </p>

      <div className={`my-7 h-px ${plan.featured ? "bg-white/15" : "bg-navy/15"}`} />
      <p className="text-4xl font-semibold tracking-[-0.06em] sm:text-5xl">{plan.price}</p>
      <p className={`mt-2 font-mono text-[9px] uppercase tracking-[0.14em] ${plan.featured ? "text-white/35" : "text-slate"}`}>
        {plan.cadence}
      </p>

      <ul className="mt-8 space-y-3" aria-label={`${plan.name} includes`}>
        {plan.features.map((feature) => (
          <li key={feature} className={`flex items-center gap-3 text-sm ${plan.featured ? "text-white/70" : "text-navy/70"}`}>
            <Check className={`size-3.5 ${plan.featured ? "text-mint" : "text-violet"}`} strokeWidth={3} aria-hidden="true" />
            {feature}
          </li>
        ))}
      </ul>

      <Link
        href="/contact"
        className={`group mt-9 flex items-center justify-between border-t pt-5 text-sm font-semibold ${
          plan.featured ? "border-white/20 hover:text-mint" : "border-navy/15 hover:text-violet"
        }`}
      >
        Choose {plan.name}
        <ArrowUpRight className="size-4 transition-transform duration-300 group-hover:-translate-y-1 group-hover:translate-x-1" aria-hidden="true" />
      </Link>
    </article>
  );
}

function PlanGroup({ number, label, note, plans }: { number: string; label: string; note: string; plans: Plan[] }) {
  return (
    <section>
      <div className="mb-7 flex items-end justify-between border-b border-navy/20 pb-5">
        <div>
          <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-violet">{number} / {label}</p>
          <h3 className="mt-3 text-2xl font-semibold tracking-[-0.045em] text-navy">{note}</h3>
        </div>
      </div>
      <div className="grid gap-7 sm:grid-cols-2">{plans.map((plan, index) => <PlanCard key={plan.name} plan={plan} index={index} />)}</div>
    </section>
  );
}

export function PricingSection() {
  return (
    <section id="pricing" className="overflow-hidden border-b border-navy/15 bg-cream py-24 sm:py-32">
      <div className="site-container">
        <div className="grid gap-10 lg:grid-cols-[0.88fr_1.12fr] lg:items-end" data-reveal>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-violet">02 / Pricing</p>
            <h2 className="mt-6 text-5xl font-semibold leading-[0.92] tracking-[-0.07em] text-navy sm:text-7xl">
              Simple numbers.
              <span className="block font-serif font-normal italic text-violet">Serious work.</span>
            </h2>
          </div>
          <div className="max-w-xl lg:justify-self-end">
            <p className="text-base leading-7 text-slate sm:text-lg">
              Choose the build that fits now. Add care if you want Keeplyn to handle hosting, maintenance, and the next round of edits.
            </p>
            <p className="mt-6 border-l-2 border-mint pl-4 text-sm font-semibold text-navy">
              Best-value pairing: Pro Build + Pro Care — $1,500 once, then $99.99/month.
            </p>
          </div>
        </div>

        <div className="mt-16 grid gap-16 xl:grid-cols-2">
          <PlanGroup number="A" label="Website build" note="Choose your starting point" plans={builds} />
          <PlanGroup number="B" label="Ongoing care" note="Choose your support level" plans={care} />
        </div>

        <div className="mt-12 flex flex-col justify-between gap-3 border-t border-navy/15 pt-5 font-mono text-[9px] uppercase tracking-[0.12em] text-slate sm:flex-row">
          <p>Prices shown in USD</p>
          <p>Scope and timeline are confirmed before work begins</p>
        </div>
      </div>
    </section>
  );
}
