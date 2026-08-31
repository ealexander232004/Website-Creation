import { notFound } from "next/navigation";
import { MossSite, NorthlineSite, SeraSite } from "@/components/demo-showcase";
import { isDemoSlug } from "@/components/demo-detail-pages";

export default async function DemoHomePage({ params }: { params: Promise<{ demo: string }> }) {
  const { demo } = await params;
  if (!isDemoSlug(demo)) notFound();

  if (demo === "moss") return <><h1 className="sr-only">Moss &amp; Mortar landscape studio</h1><MossSite /></>;
  if (demo === "northline") return <><h1 className="sr-only">Northline family dentistry</h1><NorthlineSite /></>;
  return <><h1 className="sr-only">Sera neighborhood bakery</h1><SeraSite /></>;
}
