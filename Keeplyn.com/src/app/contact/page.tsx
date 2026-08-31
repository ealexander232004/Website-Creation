import type { Metadata } from "next";
import { ContactSection, SiteFooter } from "@/components/home-sections";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Contact",
  description: "Send a general inquiry to Keeplyn.",
};

export default function ContactPage() {
  return (
    <>
      <SiteHeader />
      <main>
        <ContactSection />
      </main>
      <SiteFooter />
    </>
  );
}
