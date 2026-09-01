import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import { RequestEditor } from "@/components/request-editor";
import { SiteHeader } from "@/components/site-header";
import { editableRequestStatuses, formatRequestNumber, type WebsiteRequest } from "@/lib/customer-lifecycle";
import { WEBSITE_REQUEST_PHOTO_BUCKET } from "@/lib/website-request";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Edit website request" };
type PageProps = { params: Promise<{ id: string }> };

export default async function EditRequestPage({ params }: PageProps) {
  const requestId = Number((await params).id);
  if (!Number.isInteger(requestId) || requestId < 1) notFound();
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/start?mode=signin");
  const { data, error } = await supabase.from("website_requests").select("*, website_request_offerings(*), website_request_assets(*)").eq("id", requestId).single();
  if (error || !data) notFound();
  const request = data as WebsiteRequest;
  if (!editableRequestStatuses.includes(request.status)) redirect(`/portal/requests/${request.id}`);
  request.website_request_offerings?.sort((a, b) => a.position - b.position);
  const assets = request.website_request_assets ?? [];
  if (assets.length) {
    const { data: signed } = await supabase.storage.from(WEBSITE_REQUEST_PHOTO_BUCKET).createSignedUrls(assets.map((asset) => asset.storage_path), 3600);
    request.website_request_assets = assets.map((asset, index) => ({ ...asset, signedUrl: signed?.[index]?.signedUrl }));
  }
  return <main className="min-h-svh bg-[#050505] text-white"><SiteHeader /><section className="site-container py-12 sm:py-18"><p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9ff3b]">Request {formatRequestNumber(request.id)}</p><h1 className="mt-5 text-[clamp(3.8rem,9vw,7rem)] font-semibold leading-[0.8] tracking-[-0.08em]">Edit your brief.</h1><p className="mt-6 max-w-2xl text-sm leading-7 text-white/46">Update the information and photos Keeplyn uses to build your website. If a demo is already ready, saving will mark it for another review.</p><div className="mt-10 max-w-5xl"><RequestEditor request={request} /></div></section></main>;
}
