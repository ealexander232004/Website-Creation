import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { DemoShowcase } from "@/components/demo-showcase";
import { SiteFooter } from "@/components/home-sections";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Design Demos",
  description: "Explore three original Keeplyn website concepts across local service, healthcare, and hospitality brands.",
};

export default function DemosPage() {
  return (
    <>
      <SiteHeader />
      <main>
        <section className="overflow-hidden border-b border-navy/15 bg-cream py-20 sm:py-28">
          <div className="site-container grid gap-12 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
            <div className="reveal-on-load">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-violet">Keeplyn demos / Volume 01</p>
              <h1 className="mt-7 max-w-5xl text-6xl font-semibold leading-[0.88] tracking-[-0.075em] text-navy sm:text-8xl lg:text-[8rem]">
                Three directions.
                <span className="block font-serif font-normal italic text-violet">Zero templates.</span>
              </h1>
            </div>
            <div className="max-w-md border-t border-navy/20 pt-5 lg:justify-self-end">
              <p className="text-base leading-7 text-slate">
                Original concept brands used to explore how strategy, type, color, interface, and motion can make very different businesses feel unmistakably themselves.
              </p>
              <div className="mt-7 flex justify-between font-mono text-[9px] uppercase tracking-[0.12em] text-slate"><span>Scroll to study</span><span>03 concepts ↓</span></div>
            </div>
          </div>
        </section>

        <DemoShowcase />

        <section className="bg-cream py-24 sm:py-32">
          <div className="site-container" data-reveal>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-violet">Your business / Next</p>
            <Link href="/contact" className="group mt-7 flex items-end justify-between gap-8 border-y border-navy/20 py-10 text-navy transition-colors hover:text-violet">
              <span className="max-w-5xl text-4xl font-semibold leading-[0.95] tracking-[-0.065em] sm:text-6xl lg:text-8xl">
                Make something nobody else could own.
              </span>
              <ArrowUpRight className="mb-2 size-8 shrink-0 transition-transform duration-300 group-hover:-translate-y-2 group-hover:translate-x-2 sm:size-12" aria-hidden="true" />
            </Link>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
