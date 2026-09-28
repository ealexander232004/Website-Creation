import type { Metadata } from "next";
import { SiteFooter } from "@/components/home-sections";
import { PricingDetails } from "@/components/pricing-details";
import { SiteHeader } from "@/components/site-header";
import { PlanArt } from "@/components/site-showcase";

export const metadata: Metadata = {
  title: "Pricing",
  description: "Compare Keeplyn Starter and Pro website builds, features, hosting, and unlimited updates.",
};

export default function PricingPage() {
  return (
    <>
      <SiteHeader />
      <main className="bg-[#050505] text-white">
        <section className="site-container relative flex flex-col gap-14 py-20 sm:py-28 lg:flex-row lg:items-end lg:justify-between lg:gap-12">
          <div className="reveal-on-load">
            <h1 className="-ml-[0.065em] max-w-6xl text-[clamp(5rem,14vw,13rem)] font-semibold leading-[0.72] tracking-[-0.1em]">
              Pricing
            </h1>
            <p className="mt-10 max-w-md text-base leading-7 text-white/48">
              Choose the build that best fits your needs.
            </p>
          </div>
          <div className="pricing-hero-art w-full max-w-md shrink-0 lg:w-[min(40vw,34rem)] lg:max-w-none" aria-hidden="true">
            <PlanArt plan="pro" />
          </div>
        </section>
        <PricingDetails />
      </main>
      <SiteFooter />
    </>
  );
}
