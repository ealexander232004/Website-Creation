import { demoSlugs } from "@/components/demo-detail-pages";

export const dynamicParams = false;

export function generateStaticParams() {
  return demoSlugs.map((demo) => ({ demo }));
}

export default function DemoLayout({ children }: { children: React.ReactNode }) {
  return children;
}
