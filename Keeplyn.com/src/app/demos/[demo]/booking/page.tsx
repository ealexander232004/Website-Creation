import { notFound, redirect } from "next/navigation";
import { isDemoSlug } from "@/components/demo-detail-pages";

export default async function BookingPage({ params }: { params: Promise<{ demo: string }> }) {
  const { demo } = await params;
  if (!isDemoSlug(demo) || demo === "sera") notFound();
  redirect(`/demos?demo=${demo}&page=booking`);
}
