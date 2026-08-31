import {
  HeroSection,
  SiteFooter,
} from "@/components/home-sections";
import { PricingSection } from "@/components/pricing-section";
import { SiteHeader } from "@/components/site-header";

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main>
        <HeroSection />
        <PricingSection />
      </main>
      <SiteFooter />
    </>
  );
}
