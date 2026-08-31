import {
  HeroSection,
  SiteFooter,
} from "@/components/home-sections";
import { PricingSection } from "@/components/pricing-section";
import { ScrollExperience } from "@/components/scroll-experience";
import { SiteHeader } from "@/components/site-header";

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main>
        <HeroSection />
        <ScrollExperience />
        <PricingSection />
      </main>
      <SiteFooter />
    </>
  );
}
