import { ArrowUpRight, Check } from "lucide-react";
import Link from "next/link";
import { websitePlans } from "@/lib/plans";

export function PricingDetails() {
  return (
    <section className="bg-[#050505] pb-24 text-white sm:pb-32">
      <div className="site-container">
        <div className="overflow-hidden border border-white/14 bg-white/10">
          <div className="flex flex-col justify-between gap-4 bg-[#0b0b10] px-6 py-6 sm:flex-row sm:items-center sm:px-9">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-[#c9ff3b]">Website builds</p>
              <p className="mt-2 text-sm text-white/48">Custom design and development. No templates.</p>
            </div>
            <p className="text-xs text-white/34">50% to start · 50% at launch</p>
          </div>

          <div className="grid gap-px bg-white/12 lg:grid-cols-2">
            {websitePlans.map((plan) => (
              <article id={plan.id} key={plan.id} className="scroll-mt-24 bg-[#07070a] p-6 sm:p-9 lg:p-10">
                <div className="flex flex-col justify-between gap-8 border-b border-white/14 pb-9 sm:flex-row sm:items-start">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.16em] text-white/32">{plan.timeline}</p>
                    <h2 className="mt-3 text-5xl font-semibold tracking-[-0.075em] sm:text-6xl">{plan.name}</h2>
                    <p className="mt-4 max-w-sm text-sm leading-6 text-white/48">{plan.summary}</p>
                  </div>
                  <div className="sm:text-right">
                    <p className="text-5xl font-semibold tracking-[-0.075em]">{plan.price}</p>
                    <p className="mt-2 whitespace-nowrap text-sm text-[#c9ff3b]">+ {plan.hosting} for hosting &amp; updates</p>
                  </div>
                </div>

                <div className="divide-y divide-white/12">
                  {plan.buildDetails.map((group) => (
                    <section key={group.title} className="grid gap-5 py-8 sm:grid-cols-[0.32fr_0.68fr]">
                      <h3 className="text-[10px] font-medium uppercase tracking-[0.16em] text-white/36">{group.title}</h3>
                      <ul className="space-y-3">
                        {group.items.map((item) => (
                          <li key={item} className="flex items-start gap-3 text-sm leading-6 text-white/68">
                            <Check className="mt-1 size-3.5 shrink-0 text-[#c9ff3b]" strokeWidth={2.5} aria-hidden="true" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </section>
                  ))}
                </div>

                <section className="border border-[#7568ff]/32 bg-[#7568ff]/8 p-5 sm:p-6">
                  <p className="text-[10px] font-medium uppercase tracking-[0.16em] text-[#9f96ff]">Hosting &amp; updates · {plan.hosting}</p>
                  <ul className="mt-5 grid gap-3 sm:grid-cols-2">
                    {plan.careDetails.map((item) => (
                      <li key={item} className="flex items-start gap-3 text-xs leading-5 text-white/62">
                        <Check className="mt-0.5 size-3.5 shrink-0 text-[#9f96ff]" aria-hidden="true" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </section>

                <Link href={`/contact?plan=${plan.id}`} className="group mt-8 flex items-center justify-between border-y border-white/14 py-5 text-sm font-medium hover:border-[#c9ff3b] hover:text-[#c9ff3b]">
                  Start with {plan.name}
                  <ArrowUpRight className="size-4 transition-transform group-hover:-translate-y-1 group-hover:translate-x-1" aria-hidden="true" />
                </Link>
              </article>
            ))}
          </div>
        </div>

        <div className="mt-12 grid gap-px overflow-hidden border border-white/12 bg-white/12 sm:grid-cols-3">
          {[
            ["Payment", "50% reserves the project. The balance is due before launch."],
            ["Content", "You supply final copy and photos. Copywriting or new photography can be quoted."],
            ["Extras", "Domain fees, paid software, and third-party subscriptions are billed separately."],
          ].map(([title, detail]) => (
            <div key={title} className="bg-[#08080b] p-6">
              <p className="text-[10px] uppercase tracking-[0.16em] text-white/32">{title}</p>
              <p className="mt-4 text-sm leading-6 text-white/55">{detail}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
