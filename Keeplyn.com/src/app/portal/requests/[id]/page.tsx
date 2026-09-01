import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { ArrowLeft, ArrowRight, CheckCircle2, ExternalLink, ImageIcon, Pencil, TicketPlus } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { approveWebsite, createUpdateTicket } from "@/app/portal/actions";
import { startCheckout } from "@/app/portal/checkout-actions";
import { editableRequestStatuses, formatDate, formatRequestNumber, statusLabels, type RequestAsset, type WebsiteRequest } from "@/lib/customer-lifecycle";
import { websitePlans } from "@/lib/plans";
import { WEBSITE_REQUEST_PHOTO_BUCKET } from "@/lib/website-request";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Website request" };
type PageProps = { params: Promise<{ id: string }>; searchParams: Promise<{ payment?: string }> };

export default async function RequestDetailsPage({ params, searchParams }: PageProps) {
  const [{ id }, query] = await Promise.all([params, searchParams]);
  const requestId = Number(id);
  if (!Number.isInteger(requestId) || requestId < 1) notFound();
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/start?mode=signin");
  const { data, error } = await supabase.from("website_requests").select("*, website_request_offerings(*), website_request_assets(*), website_request_updates(*)").eq("id", requestId).single();
  if (error || !data) notFound();
  const request = data as WebsiteRequest;
  request.website_request_offerings?.sort((a, b) => a.position - b.position);
  request.website_request_updates?.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  const rawAssets = request.website_request_assets ?? [];
  if (rawAssets.length) {
    const { data: signed } = await supabase.storage.from(WEBSITE_REQUEST_PHOTO_BUCKET).createSignedUrls(rawAssets.map((asset) => asset.storage_path), 3600);
    request.website_request_assets = rawAssets.map((asset, index) => ({ ...asset, signedUrl: signed?.[index]?.signedUrl }));
  }
  const plan = websitePlans.find((item) => item.id === request.plan_id)!;
  const editable = editableRequestStatuses.includes(request.status);
  const canTicket = request.status === "demo_ready" || request.status === "changes_requested" || (request.status === "live" && request.hosting_selected);
  const openTickets = request.website_request_updates?.filter((ticket) => ticket.status !== "completed").length ?? 0;

  return (
    <main className="min-h-svh bg-[#050505] text-white">
      <SiteHeader />
      <section className="site-container py-12 sm:py-18">
        <Link href="/portal" className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-white/38 hover:text-white"><ArrowLeft className="size-3.5" />All requests</Link>
        {query.payment === "success" ? <div className="mt-8 border border-[#c9ff3b]/35 bg-[#c9ff3b]/8 px-5 py-4 text-sm text-[#dcffa2]">Stripe received your checkout. Payment confirmation can take a moment; this page updates when the signed webhook arrives.</div> : null}
        <div className="mt-8 flex flex-col gap-8 border-b border-white/10 pb-10 lg:flex-row lg:items-end lg:justify-between">
          <div><p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9ff3b]">Request {formatRequestNumber(request.id)}</p><h1 className="mt-5 text-[clamp(3.6rem,9vw,7rem)] font-semibold capitalize leading-[0.8] tracking-[-0.08em]">{request.plan_id} website</h1><p className="mt-6 text-sm text-white/44">Created {formatDate(request.created_at)} · {statusLabels[request.status]}</p></div>
          <div className="flex flex-wrap gap-3">
            {editable ? <Link href={`/portal/requests/${request.id}/edit`} className="button-secondary"><Pencil className="size-4" />Edit request & photos</Link> : null}
            {request.demo_url ? <a href={request.demo_url} target="_blank" rel="noreferrer" className="button-primary">View demo <ExternalLink className="size-4" /></a> : null}
            {request.live_url ? <a href={request.live_url} target="_blank" rel="noreferrer" className="button-primary">Visit live website <ExternalLink className="size-4" /></a> : null}
          </div>
        </div>

        <div className="mt-8 grid gap-8 xl:grid-cols-[minmax(0,1fr)_22rem]">
          <div className="space-y-8">
            {request.status === "demo_ready" || request.status === "changes_requested" ? (
              <section className="border border-[#c9ff3b]/28 bg-[#c9ff3b]/[0.045] p-6 sm:p-8">
                <CheckCircle2 className="size-7 text-[#c9ff3b]" />
                <h2 className="mt-5 text-3xl font-semibold tracking-[-0.05em]">Ready to decide?</h2>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-white/48">Review the demo. If it’s exactly right and there are no open update tickets, approve it to begin domain setup.</p>
                <form action={approveWebsite} className="mt-6"><input type="hidden" name="requestId" value={request.id} /><button className="button-primary" disabled={openTickets > 0}>Approve website <ArrowRight className="size-4" /></button>{openTickets ? <p className="mt-3 text-xs text-[#ffb4a8]">Complete {openTickets} open update {openTickets === 1 ? "ticket" : "tickets"} before approval.</p> : null}</form>
              </section>
            ) : null}
            {request.status === "domain_pending" || (request.status === "payment_pending" && request.payment_status === "ready") ? (
              <section className="border border-white/14 bg-white/[0.025] p-6 sm:p-8"><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#c9ff3b]">Next step</p><h2 className="mt-4 text-3xl font-semibold tracking-[-0.05em]">Set up your domain.</h2><p className="mt-3 text-sm leading-6 text-white/46">Buy a domain if you need one, enter it, choose optional care, then continue to Stripe.</p><Link href={`/portal/requests/${request.id}/domain`} className="button-primary mt-6">Domain setup <ArrowRight className="size-4" /></Link></section>
            ) : null}
            {request.status === "payment_pending" && ["pending", "failed"].includes(request.payment_status) ? (
              <section className="border border-white/14 bg-white/[0.025] p-6 sm:p-8"><h2 className="text-3xl font-semibold tracking-[-0.05em]">{request.payment_status === "failed" ? "Payment needs another try." : "Checkout is ready."}</h2><p className="mt-3 text-sm leading-6 text-white/46">Your domain is <strong className="text-white/72">{request.domain_name}</strong>. Continue to Stripe’s secure checkout when you’re ready.</p><form action={startCheckout} className="mt-6"><input type="hidden" name="requestId" value={request.id} /><button className="button-primary">Continue to Stripe <ArrowRight className="size-4" /></button></form></section>
            ) : null}

            <section className="border border-white/12 bg-white/[0.02] p-6 sm:p-8"><div className="flex items-end justify-between gap-4"><div><p className="text-[10px] uppercase tracking-[0.16em] text-white/30">Your brief</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.05em]">Request details</h2></div><span className="text-sm font-semibold text-[#c9ff3b]">{plan.price}</span></div><dl className="mt-8 grid gap-7 sm:grid-cols-2"><Detail label="Plan" value={`${plan.name} website`} /><Detail label="Care plan" value={request.hosting_selected ? plan.hosting : "Not selected yet"} /><Detail label="Photo direction" value={request.photo_brief || "Open to Keeplyn’s direction"} /><Detail label="Theme" value={request.theme_description || "Open to Keeplyn’s direction"} /><div className="sm:col-span-2"><Detail label="Additional notes" value={request.additional_notes || "No additional notes"} /></div></dl></section>

            <section className="border border-white/12 bg-white/[0.02] p-6 sm:p-8"><h2 className="text-3xl font-semibold tracking-[-0.05em]">Offerings</h2><div className="mt-6 divide-y divide-white/10 border-y border-white/10">{request.website_request_offerings?.map((offering) => <div key={offering.id} className="grid gap-2 py-5 sm:grid-cols-[1fr_auto]"><div><h3 className="font-semibold">{offering.title}</h3><p className="mt-2 text-sm leading-6 text-white/44">{offering.description}</p></div><p className="text-sm font-semibold text-[#c9ff3b]">${Number(offering.price).toFixed(2)}</p></div>)}</div></section>

            <section className="border border-white/12 bg-white/[0.02] p-6 sm:p-8"><h2 className="text-3xl font-semibold tracking-[-0.05em]">Photos</h2>{request.website_request_assets?.length ? <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-3">{request.website_request_assets.map((asset: RequestAsset) => asset.signedUrl ? <a key={asset.id} href={asset.signedUrl} target="_blank" rel="noreferrer" className="group block"><Image unoptimized src={asset.signedUrl} alt={asset.original_filename} width={600} height={600} className="aspect-square w-full object-cover opacity-80 transition group-hover:opacity-100" /><span className="mt-2 block truncate text-[10px] text-white/34">{asset.original_filename}</span></a> : null)}</div> : <p className="mt-4 flex items-center gap-2 text-sm text-white/38"><ImageIcon className="size-4" />No photos uploaded.</p>}</section>

            <section className="border border-white/12 bg-white/[0.02] p-6 sm:p-8"><h2 className="text-3xl font-semibold tracking-[-0.05em]">Update tickets</h2>{request.website_request_updates?.length ? <div className="mt-6 space-y-3">{request.website_request_updates.map((ticket) => <article key={ticket.id} className="border border-white/10 p-5"><div className="flex justify-between gap-3"><h3 className="font-semibold">{ticket.title}</h3><span className="text-[10px] uppercase tracking-[0.12em] text-[#c9ff3b]">{ticket.status.replace("_", " ")}</span></div><p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-white/46">{ticket.description}</p>{ticket.admin_response ? <p className="mt-4 border-l-2 border-[#c9ff3b] pl-4 text-sm leading-6 text-white/62"><strong>Keeplyn:</strong> {ticket.admin_response}</p> : null}</article>)}</div> : <p className="mt-4 text-sm text-white/38">No update tickets yet.</p>}{canTicket ? <form action={createUpdateTicket} className="mt-8 space-y-4 border-t border-white/10 pt-6"><input type="hidden" name="requestId" value={request.id} /><label className="block text-xs font-semibold text-white/62">Update title<input name="title" required minLength={2} maxLength={120} className="mt-2 w-full border border-white/14 bg-black/20 px-4 py-3 text-white outline-none focus:border-[#c9ff3b]" placeholder="Adjust the home page headline" /></label><label className="block text-xs font-semibold text-white/62">What should change?<textarea name="description" required minLength={2} maxLength={5000} className="mt-2 min-h-36 w-full resize-y border border-white/14 bg-black/20 px-4 py-3 text-white outline-none focus:border-[#c9ff3b]" placeholder="Tell us exactly what you want updated…" /></label><button className="button-primary"><TicketPlus className="size-4" />Send update ticket</button></form> : null}</section>
          </div>

          <aside className="h-fit border border-white/12 bg-white/[0.025] p-6 xl:sticky xl:top-24"><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">Progress</p><ol className="mt-6 space-y-5"><Progress done label="Request received" /><Progress done={!["submitted", "in_review", "in_progress"].includes(request.status)} label="Demo delivered" /><Progress done={Boolean(request.approved_at)} label="Website approved" /><Progress done={Boolean(request.paid_at)} label="Domain & payment" /><Progress done={request.status === "live"} label="Website live" /></ol>{request.domain_name ? <div className="mt-7 border-t border-white/10 pt-5"><p className="text-[10px] uppercase tracking-[0.14em] text-white/28">Domain</p><p className="mt-2 break-all text-sm text-white/68">{request.domain_name}</p></div> : null}</aside>
        </div>
      </section>
    </main>
  );
}

function Detail({ label, value }: { label: string; value: string }) { return <div><dt className="text-[10px] uppercase tracking-[0.14em] text-white/28">{label}</dt><dd className="mt-2 whitespace-pre-wrap text-sm leading-6 text-white/62">{value}</dd></div>; }
function Progress({ done, label }: { done: boolean; label: string }) { return <li className="flex items-center gap-3"><span className={`grid size-6 place-items-center rounded-full border ${done ? "border-[#c9ff3b] bg-[#c9ff3b] text-black" : "border-white/16 text-transparent"}`}><CheckCircle2 className="size-3.5" /></span><span className={done ? "text-sm text-white/72" : "text-sm text-white/30"}>{label}</span></li>; }
