import type { Metadata } from "next";
import { DemoShowcase } from "@/components/demo-showcase";
import { SiteFooter } from "@/components/home-sections";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Design Demos",
  description: "Explore three complete original websites designed and developed by Keeplyn.",
};

export default function DemosPage() {
  return (
    <>
      <SiteHeader />
      <main>
        <DemoShowcase />
      </main>
      <SiteFooter />
    </>
  );
}
