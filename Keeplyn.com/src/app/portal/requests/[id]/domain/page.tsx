import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { ArrowLeft, ArrowRight, ExternalLink, Globe2, ShieldCheck } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { saveDomainAndCheckout } from "@/app/portal/checkout-actions";
import type { WebsiteRequest } from "@/lib/customer-lifecycle";
import { websitePlans } from "@/lib/plans";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Domain setup" };
type PageProps = { params: Promise<{ id: string }> };

export default async function DomainSetupPage({ params }: PageProps) {
  const requestId = Number((await params).id);
  if (!Number.isInteger(requestId) || requestId < 1) notFound();
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/start?mode=signin");
  const { data, error } = await supabase.from("website_requests").select("*").eq("id", requestId).single();
  if (error || !data) notFound();
  const request = data as WebsiteRequest;
  if (!request.approved_at) redirect(`/portal/requests/${request.id}`);
  const plan = websitePlans.find((item) => item.id === request.plan_id)!;

  return <main className="min-h-svh bg-[#050505] text-white"><SiteHeader /><section className="site-container py-12 sm:py-20"><Link href={`/portal/requests/${request.id}`} className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-white/38 hover:text-white"><ArrowLeft className="size-3.5" />Request details</Link><div className="mt-10 grid gap-10 lg:grid-cols-[minmax(0,1fr)_24rem] lg:gap-16"><div><p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9ff3b]">Approved · Final setup</p><h1 className="mt-5 text-[clamp(4rem,10vw,8rem)] font-semibold leading-[0.78] tracking-[-0.085em]">Choose your address.</h1><p className="mt-7 max-w-2xl text-sm leading-7 text-white/48">Your website is approved. Buy a domain if you need one, enter it below, then continue to Stripe for the first and only required payment.</p><a href="https://porkbun.com/products/domains" target="_blank" rel="noreferrer" className="button-secondary mt-7"><Globe2 className="size-4" />Buy a domain at Porkbun <ExternalLink className="size-3.5" /></a><form action={saveDomainAndCheckout} className="mt-10 max-w-2xl space-y-6 border-t border-white/10 pt-8"><input type="hidden" name="requestId" value={request.id} /><label className="block text-xs font-semibold text-white/62">Domain you own<input name="domain" required defaultValue={request.domain_name ?? ""} className="mt-2 w-full border border-white/14 bg-white/[0.045] px-4 py-4 text-lg text-white outline-none focus:border-[#c9ff3b]" placeholder="yourbusiness.com" /></label><label className="flex cursor-pointer items-start gap-4 border border-white/14 bg-white/[0.025] p-5"><input type="checkbox" name="hosting" defaultChecked={request.hosting_selected} className="mt-1 size-4 accent-[#c9ff3b]" /><span><span className="block font-semibold">Add Keeplyn care · {plan.hosting}</span><span className="mt-2 block text-sm leading-6 text-white/42">Hosting, maintenance, and content updates completed in under two business days.</span></span></label><div className="flex items-start gap-3 border border-[#c9ff3b]/22 bg-[#c9ff3b]/[0.04] p-4 text-xs leading-5 text-white/48"><ShieldCheck className="mt-0.5 size-4 shrink-0 text-[#c9ff3b]" />No card details are collected by Keeplyn. The next page is Stripe’s secure checkout.</div><button className="button-primary">Save domain & continue to Stripe <ArrowRight className="size-4" /></button></form></div><aside className="h-fit border border-white/12 bg-white/[0.025] p-6 lg:sticky lg:top-24"><p className="text-[10px] uppercase tracking-[0.15em] text-white/28">Approved build</p><p className="mt-3 text-4xl font-semibold tracking-[-0.06em]">{plan.price}</p><p className="mt-3 text-sm text-white/42">One-time {plan.name} website build</p><div className="mt-7 border-t border-white/10 pt-5 text-xs leading-5 text-white/34">You were not charged during the request, design, demo, or revision stages.</div></aside></div></section></main>;
}
