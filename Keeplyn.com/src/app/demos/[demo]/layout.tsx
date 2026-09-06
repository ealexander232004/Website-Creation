import { notFound } from "next/navigation";
import { demoSlugs, isDemoSlug } from "@/components/templates/catalog";
import { DemoToolbar } from "@/components/templates/template-chrome";
import { templateFonts } from "@/components/templates/typography";
import "@/components/templates/templates.css";

export const dynamicParams = false;
export function generateStaticParams() {
  return demoSlugs.map((demo) => ({ demo }));
}

export default async function DemoSiteLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ demo: string }>;
}) {
  const { demo } = await params;
  if (!isDemoSlug(demo)) notFound();
  return (
    <div className={templateFonts}>
      <DemoToolbar active={demo} />
      <main>{children}</main>
    </div>
  );
}
