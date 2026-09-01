import type { Metadata } from "next";
import { DemoShowcase, type DemoPage } from "@/components/demo-showcase";
import { isDemoSlug } from "@/components/demo-detail-pages";
import { SiteFooter } from "@/components/home-sections";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Design Demos",
  description: "Explore three complete original websites designed and developed by Keeplyn.",
};

type DemosPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function DemosPage({ searchParams }: DemosPageProps) {
  const query = await searchParams;
  const demoValue = Array.isArray(query.demo) ? query.demo[0] : query.demo;
  const pageValue = Array.isArray(query.page) ? query.page[0] : query.page;
  const initialDemo = demoValue && isDemoSlug(demoValue) ? demoValue : "moss";
  const initialPage: DemoPage = pageValue === "about" || pageValue === "faq" || pageValue === "pricing" || pageValue === "contact" || pageValue === "booking" ? pageValue : "home";

  return (
    <>
      <SiteHeader />
      <main>
        <DemoShowcase initialDemo={initialDemo} initialPage={initialPage} />
      </main>
      <SiteFooter />
    </>
  );
}
