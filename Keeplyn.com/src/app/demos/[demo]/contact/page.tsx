import { notFound } from "next/navigation";
import { DemoContactPage, isDemoSlug } from "@/components/demo-detail-pages";

export default async function ContactPage({ params }: { params: Promise<{ demo: string }> }) {
  const { demo } = await params;
  if (!isDemoSlug(demo)) notFound();

  return <DemoContactPage demo={demo} />;
}
