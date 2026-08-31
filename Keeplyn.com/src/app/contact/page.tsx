import type { Metadata } from "next";
import { ContactSection, SiteFooter } from "@/components/home-sections";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Contact",
  description: "Start a conversation with Keeplyn about a new website, redesign, or ongoing website care.",
};

const prompts = [
  ["What you do", "A sentence or two about the business and the people you serve."],
  ["What feels stuck", "The current website, a missing site, unclear messaging, or something else."],
  ["What comes next", "The launch, offer, growth goal, or deadline the new site should support."],
];

export default function ContactPage() {
  return (
    <>
      <SiteHeader />
      <main>
        <ContactSection />
        <section className="border-b border-navy/15 bg-cream py-20 sm:py-24">
          <div className="site-container">
            <div className="grid gap-10 lg:grid-cols-[0.65fr_1.35fr]" data-reveal>
              <div>
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-violet">A useful first note</p>
                <h2 className="mt-5 text-3xl font-semibold tracking-[-0.055em] text-navy sm:text-4xl">No formal brief required.</h2>
              </div>
              <div className="grid border-y border-navy/15 sm:grid-cols-3 sm:divide-x sm:divide-navy/15">
                {prompts.map(([title, description], index) => (
                  <article key={title} className="border-b border-navy/15 py-7 last:border-b-0 sm:border-b-0 sm:px-7 sm:first:pl-0 sm:last:pr-0">
                    <p className="font-mono text-[9px] text-violet">0{index + 1}</p>
                    <h3 className="mt-8 text-lg font-semibold tracking-[-0.035em] text-navy">{title}</h3>
                    <p className="mt-3 text-sm leading-6 text-slate">{description}</p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
