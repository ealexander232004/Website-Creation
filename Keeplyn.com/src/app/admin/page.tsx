import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { ArrowRight, LayoutDashboard } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { formatDate, formatRequestNumber, statusLabels, type WebsiteRequest } from "@/lib/customer-lifecycle";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Admin workspace" };

export default async function AdminPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/start?mode=signin");
  const { data: admin } = await supabase.rpc("is_keeplyn_admin");
  if (!admin) redirect("/portal");
  const { data, error } = await supabase.from("website_requests").select("*").order("updated_at", { ascending: false });
  if (error) throw new Error(error.message);
  const requests = (data ?? []) as WebsiteRequest[];
  return <main className="min-h-svh bg-[#050505] text-white"><SiteHeader /><section className="site-container py-14 sm:py-20"><div className="flex flex-col gap-7 border-b border-white/10 pb-10 sm:flex-row sm:items-end sm:justify-between"><div><p className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9ff3b]"><LayoutDashboard className="size-3.5" />Keeplyn operations</p><h1 className="mt-5 text-[clamp(4rem,10vw,8rem)] font-semibold leading-[0.78] tracking-[-0.085em]">Build queue.</h1></div><Link href="/portal" className="button-secondary">Customer portal</Link></div><div className="mt-10 overflow-x-auto border border-white/12"><table className="w-full min-w-[760px] border-collapse text-left"><thead className="border-b border-white/10 bg-white/[0.035] text-[10px] uppercase tracking-[0.15em] text-white/30"><tr><th className="px-5 py-4">Request</th><th className="px-5 py-4">Customer</th><th className="px-5 py-4">Plan</th><th className="px-5 py-4">Status</th><th className="px-5 py-4">Updated</th><th className="px-5 py-4" /></tr></thead><tbody className="divide-y divide-white/10">{requests.map((request) => <tr key={request.id} className="bg-white/[0.015]"><td className="px-5 py-5 font-semibold">{formatRequestNumber(request.id)}</td><td className="px-5 py-5"><span className="block text-sm text-white/72">{request.customer_name || "Customer"}</span><span className="mt-1 block text-xs text-white/32">{request.customer_email}</span></td><td className="px-5 py-5 text-sm capitalize text-white/62">{request.plan_id}</td><td className="px-5 py-5 text-sm text-[#c9ff3b]">{statusLabels[request.status]}</td><td className="px-5 py-5 text-xs text-white/36">{formatDate(request.updated_at)}</td><td className="px-5 py-5"><Link href={`/admin/requests/${request.id}`} className="inline-flex items-center gap-2 text-xs font-semibold text-white/52 hover:text-white">Open <ArrowRight className="size-3.5" /></Link></td></tr>)}{!requests.length ? <tr><td colSpan={6} className="px-5 py-16 text-center text-sm text-white/38">No website requests yet.</td></tr> : null}</tbody></table></div></section></main>;
}
