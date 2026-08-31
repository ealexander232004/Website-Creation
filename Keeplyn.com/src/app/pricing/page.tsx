import type { Metadata } from "next";
import { SiteFooter } from "@/components/home-sections";
import { PricingDetails } from "@/components/pricing-details";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Pricing",
  description: "Compare Keeplyn Starter and Pro website builds, features, hosting, and unlimited updates.",
};

export default function PricingPage() {
  return (
    <>
      <SiteHeader />
      <main className="bg-[#050505] text-white">
        <section className="site-container py-20 sm:py-28">
          <h1 className="max-w-6xl text-[clamp(5rem,14vw,13rem)] font-semibold leading-[0.72] tracking-[-0.1em]">
            Pricing
          </h1>
          <p className="mt-10 max-w-md text-base leading-7 text-white/48">
            Choose the build that best fits your needs.
          </p>
        </section>
        <PricingDetails />
      </main>
      <SiteFooter />
    </>
  );
}
