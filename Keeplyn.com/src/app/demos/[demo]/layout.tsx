import { demoSlugs } from "@/components/demo-detail-pages";
import { SiteFooter } from "@/components/home-sections";
import { SiteHeader } from "@/components/site-header";

export const dynamicParams = false;

export function generateStaticParams() {
  return demoSlugs.map((demo) => ({ demo }));
}

export default function DemoSiteLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <SiteHeader />
      <main className="bg-[#050505]">{children}</main>
      <SiteFooter />
    </>
  );
}
