import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  isDemoSlug,
  templates,
  demoHref,
} from "@/components/templates/catalog";
import { DemoWebsite } from "@/components/templates/template-pages";

type Props = { params: Promise<{ demo: string }> };
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { demo } = await params;
  if (!isDemoSlug(demo)) notFound();
  const b = templates[demo];
  const title = `Our story / ${b.name}`;
  const description = `${b.category} concept website by Keeplyn. ${b.intro}`;
  return {
    title,
    description,
    alternates: { canonical: demoHref(demo, "about") },
    openGraph: { title, description, url: demoHref(demo, "about") },
  };
}
export default async function DemoPage({ params }: Props) {
  const { demo } = await params;
  if (!isDemoSlug(demo)) notFound();
  return <DemoWebsite demo={demo} page="about" />;
}
