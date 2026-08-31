import { ArrowRight, Check, Sparkles } from "lucide-react";
import { SectionHeading } from "./section-heading";

interface PricingCardProps {
  name: string;
  price: string;
  suffix?: string;
  description: string;
  features: string[];
  recommended?: boolean;
}

function PricingCard({
  name,
  price,
  suffix,
  description,
  features,
  recommended = false,
}: PricingCardProps) {
  return (
    <article
      className={`relative flex h-full flex-col rounded-[1.75rem] border p-6 sm:p-8 ${
        recommended
          ? "border-violet bg-navy text-white shadow-2xl shadow-navy/20"
          : "border-navy/10 bg-white text-navy shadow-sm shadow-navy/5"
      }`}
    >
      {recommended ? (
        <div className="absolute -top-3.5 left-6 flex items-center gap-1.5 rounded-full bg-mint px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.12em] text-navy shadow-lg shadow-mint/15">
          <Sparkles className="size-3" aria-hidden="true" />
          Recommended
        </div>
      ) : null}
      <h3 className="text-lg font-bold">{name}</h3>
      <p className={`mt-2 min-h-12 text-sm leading-6 ${recommended ? "text-white/55" : "text-slate"}`}>
        {description}
      </p>
      <div className="mt-6 flex items-end gap-1.5">
        <span className="text-4xl font-bold tracking-[-0.06em]">{price}</span>
        {suffix ? (
          <span className={`pb-1 text-sm ${recommended ? "text-white/45" : "text-slate"}`}>
            {suffix}
          </span>
        ) : null}
      </div>
      <div className={`my-7 h-px ${recommended ? "bg-white/10" : "bg-navy/8"}`} />
      <ul className="space-y-3.5" aria-label={`${name} includes`}>
        {features.map((feature) => (
          <li key={feature} className="flex gap-3 text-sm leading-5">
            <span className={`mt-0.5 grid size-5 shrink-0 place-items-center rounded-full ${recommended ? "bg-mint text-navy" : "bg-violet/10 text-violet"}`}>
              <Check className="size-3" strokeWidth={3} aria-hidden="true" />
            </span>
            <span className={recommended ? "text-white/78" : "text-navy/75"}>{feature}</span>
          </li>
        ))}
      </ul>
      <a
        href="#contact"
        className={`mt-8 flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm font-bold transition-all ${
          recommended
            ? "bg-mint text-navy hover:-translate-y-0.5 hover:bg-white"
            : "border border-navy/12 bg-mist text-navy hover:border-violet/30 hover:bg-violet/5"
        }`}
      >
        Choose {name}
        <ArrowRight className="size-4" aria-hidden="true" />
      </a>
    </article>
  );
}

const builds = [
  {
    name: "Starter",
    price: "$750",
    description: "A focused, professional website for a clear service or offer.",
    features: [
      "Up to 4 thoughtfully designed pages",
      "Mobile-first responsive build",
      "Contact form setup",
      "Foundational on-page SEO",
      "One structured revision round",
    ],
  },
  {
    name: "Pro",
    price: "$1,500",
    description: "A more strategic website built to support growth and multiple offers.",
    features: [
      "Up to 8 custom-designed pages",
      "Messaging and content guidance",
      "Conversion-focused page strategy",
      "Blog or simple CMS setup",
      "Analytics and key integrations",
      "Three structured revision rounds",
    ],
    recommended: true,
  },
];

const care = [
  {
    name: "Starter Care",
    price: "$49.99",
    suffix: "/ month",
    description: "Reliable essentials that keep your website fast, secure, and online.",
    features: [
      "Managed website hosting",
      "SSL, security, and backups",
      "Core software updates",
      "30 minutes of content updates monthly",
      "Standard email support",
    ],
  },
  {
    name: "Pro Care",
    price: "$99.99",
    suffix: "/ month",
    description: "Proactive support for businesses that want to keep improving.",
    features: [
      "Everything in Starter Care",
      "90 minutes of content updates monthly",
      "Priority support queue",
      "Monthly performance check",
      "Quarterly conversion recommendations",
    ],
    recommended: true,
  },
];

export function PricingSection() {
  return (
    <section id="pricing" className="section-space bg-mist">
      <div className="site-container">
        <SectionHeading
          eyebrow="Clear, honest pricing"
          title="Invest once. Stay supported as you grow."
          description="Start with the build that fits your business, then choose the care plan that matches how often you need support. No mystery quotes or padded retainers."
          align="center"
        />

        <div className="mx-auto mt-10 flex max-w-3xl items-center justify-center gap-3 rounded-2xl border border-violet/15 bg-white p-4 text-center shadow-sm sm:text-left">
          <span className="hidden size-9 shrink-0 place-items-center rounded-xl bg-violet/10 text-violet sm:grid">
            <Sparkles className="size-4" aria-hidden="true" />
          </span>
          <p className="text-sm leading-6 text-slate">
            <strong className="text-navy">Best-value pairing:</strong> Pro Website Build + Pro Care for <strong className="text-navy">$1,500 once + $99.99/month.</strong>
          </p>
        </div>

        <div className="mt-14 grid gap-12 lg:grid-cols-2 lg:gap-16">
          <div>
            <div className="mb-7">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-violet">Step 1</p>
              <h3 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-navy">Website Build</h3>
              <p className="mt-2 text-sm text-slate">One-time project investment</p>
            </div>
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
              {builds.map((plan) => (
                <PricingCard key={plan.name} {...plan} />
              ))}
            </div>
          </div>

          <div>
            <div className="mb-7">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-violet">Step 2</p>
              <h3 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-navy">Hosting + Updates</h3>
              <p className="mt-2 text-sm text-slate">Ongoing monthly care</p>
            </div>
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
              {care.map((plan) => (
                <PricingCard key={plan.name} {...plan} />
              ))}
            </div>
          </div>
        </div>

        <p className="mt-8 text-center text-xs leading-5 text-slate/75">
          Prices shown in USD. Final scope and timeline are confirmed before work begins.
        </p>
      </div>
    </section>
  );
}
