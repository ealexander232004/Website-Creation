import { notFound, redirect } from "next/navigation";
import { isDemoSlug } from "@/components/demo-detail-pages";

type DemoAboutRouteProps = {
  params: Promise<{ demo: string }>;
};

export default async function DemoAboutRoute({ params }: DemoAboutRouteProps) {
  const { demo } = await params;
  if (!isDemoSlug(demo)) notFound();
  redirect(`/demos?demo=${demo}&page=about`);
}
