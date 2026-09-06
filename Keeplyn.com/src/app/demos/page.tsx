import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { DemoShowcase } from "@/components/demo-showcase";
import {
  demoHref,
  isDemoSlug,
  isDemoPage,
} from "@/components/templates/catalog";
import { SiteFooter } from "@/components/home-sections";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Website Templates & Design Demos",
  description:
    "Three distinct Keeplyn website templates: a cinematic landscape portfolio, a fresh dental studio, and a bold neighborhood bakery.",
};

export default async function DemosPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  const demo = Array.isArray(query.demo) ? query.demo[0] : query.demo;
  const page = Array.isArray(query.page) ? query.page[0] : query.page;
  // Preserve links shared from the previous tabbed showcase.
  if (demo && isDemoSlug(demo))
    redirect(demoHref(demo, page && isDemoPage(page) ? page : "home"));
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
