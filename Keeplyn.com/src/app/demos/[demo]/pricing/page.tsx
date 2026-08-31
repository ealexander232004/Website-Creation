import { notFound } from "next/navigation";
import { DemoPricingPage, isDemoSlug } from "@/components/demo-detail-pages";

export default async function PricingPage({ params }: { params: Promise<{ demo: string }> }) {
  const { demo } = await params;
  if (!isDemoSlug(demo)) notFound();

  return <DemoPricingPage demo={demo} />;
}
