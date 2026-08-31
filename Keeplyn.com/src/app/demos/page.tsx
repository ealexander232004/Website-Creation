import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { DemoShowcase } from "@/components/demo-showcase";
import { SiteFooter } from "@/components/home-sections";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Design Demos",
  description: "Explore three original Keeplyn website concepts.",
};

export default function DemosPage() {
  return (
    <>
      <SiteHeader />
      <main>
        <section className="bg-[#050505] py-20 text-white sm:py-28">
          <div className="site-container">
            <h1 className="text-[clamp(6rem,18vw,17rem)] font-semibold leading-[0.72] tracking-[-0.1em]">
              Demos.
            </h1>
            <p className="mt-10 text-base text-white/45">Three directions. Zero templates.</p>
          </div>
        </section>

        <DemoShowcase />

        <section className="bg-[#050505] pb-24 text-white sm:pb-32">
          <div className="site-container">
            <Link href="/contact" className="group flex items-end justify-between gap-8 border-y border-white/15 py-10 transition-colors hover:text-[#c9ff3b]">
              <span className="max-w-5xl text-4xl font-semibold leading-[0.95] tracking-[-0.065em] sm:text-6xl lg:text-8xl">
                Make yours.
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
