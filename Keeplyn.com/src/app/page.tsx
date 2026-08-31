import {
  HeroSection,
  SiteFooter,
} from "@/components/home-sections";
import { HelixScene } from "@/components/helix-scene";
import { PricingSection } from "@/components/pricing-section";
import { SiteHeader } from "@/components/site-header";

export default function Home() {
  return (
    <>
      <SiteHeader />
      <div className="relative isolate overflow-clip bg-[#050505]">
        <div className="pointer-events-none fixed inset-0 z-0 opacity-95" aria-hidden="true">
          <HelixScene />
        </div>
        <div className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(circle_at_center,rgba(5,5,5,0.18)_0%,rgba(5,5,5,0.76)_43%,rgba(5,5,5,0.08)_74%,rgba(5,5,5,0.42)_100%)]" aria-hidden="true" />
        <main className="relative z-10">
          <HeroSection />
          <PricingSection />
        </main>
      </div>
      <SiteFooter />
    </>
  );
}
