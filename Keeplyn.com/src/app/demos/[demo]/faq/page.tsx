import { notFound, redirect } from "next/navigation";
import { isDemoSlug } from "@/components/demo-detail-pages";

type DemoFaqRouteProps = {
  params: Promise<{ demo: string }>;
};

export default async function DemoFaqRoute({ params }: DemoFaqRouteProps) {
  const { demo } = await params;
  if (!isDemoSlug(demo)) notFound();
  redirect(`/demos?demo=${demo}&page=faq`);
}
