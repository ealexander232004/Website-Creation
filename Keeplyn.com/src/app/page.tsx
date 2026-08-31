import { DemoShowcase } from "@/components/demo-showcase";
import { FaqSection } from "@/components/faq-section";
import {
  BenefitsSection,
  ContactSection,
  HeroSection,
  ProcessSection,
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
        <ProcessSection />
        <DemoShowcase />
        <BenefitsSection />
        <PricingSection />
        <FaqSection />
        <ContactSection />
      </main>
      <SiteFooter />
    </>
  );
}
