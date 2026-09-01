import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { ArrowRight, CirclePlus, ShieldCheck } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { formatDate, formatRequestNumber, statusLabels, type WebsiteRequest } from "@/lib/customer-lifecycle";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Customer portal", description: "Manage your Keeplyn website requests, demos, updates, domain, and launch." };

export default async function PortalPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/start?mode=signin");
  const [{ data, error }, { data: admin }] = await Promise.all([
    supabase.from("website_requests").select("*").order("created_at", { ascending: false }),
    supabase.rpc("is_keeplyn_admin"),
  ]);
  if (error) throw new Error(error.message);
  const requests = (data ?? []) as WebsiteRequest[];

  return (
    <main className="min-h-svh bg-[#050505] text-white">
      <SiteHeader />
      <section className="site-container py-16 sm:py-24">
        <div className="flex flex-col gap-8 border-b border-white/10 pb-12 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9ff3b]">Customer portal</p>
            <h1 className="mt-5 text-[clamp(4rem,10vw,8rem)] font-semibold leading-[0.78] tracking-[-0.085em]">Your websites.</h1>
            <p className="mt-7 max-w-2xl text-sm leading-7 text-white/48">Start a request, review demos, send revisions, and follow every website through launch.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            {admin ? <Link href="/admin" className="button-secondary"><ShieldCheck className="size-4" aria-hidden="true" />Admin workspace</Link> : null}
            <Link href="/start" className="button-primary"><CirclePlus className="size-4" aria-hidden="true" />New website request</Link>
          </div>
        </div>

        {requests.length ? (
          <div className="mt-10 grid gap-4 lg:grid-cols-2">
            {requests.map((request) => (
              <Link key={request.id} href={`/portal/requests/${request.id}`} className="group border border-white/12 bg-white/[0.025] p-6 transition hover:border-[#c9ff3b]/55 hover:bg-white/[0.045] sm:p-8">
                <div className="flex items-start justify-between gap-5">
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#c9ff3b]">Request {formatRequestNumber(request.id)}</p>
                    <h2 className="mt-4 text-4xl font-semibold capitalize tracking-[-0.06em]">{request.plan_id} website</h2>
                  </div>
                  <ArrowRight className="size-5 text-white/28 transition group-hover:translate-x-1 group-hover:text-[#c9ff3b]" aria-hidden="true" />
                </div>
                <div className="mt-12 flex items-end justify-between gap-4 border-t border-white/10 pt-5">
                  <div><p className="text-[10px] uppercase tracking-[0.14em] text-white/28">Status</p><p className="mt-2 text-sm font-semibold text-white/78">{statusLabels[request.status]}</p></div>
                  <p className="text-xs text-white/32">Updated {formatDate(request.updated_at)}</p>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="mt-10 border border-dashed border-white/18 px-6 py-20 text-center">
            <p className="text-3xl font-semibold tracking-[-0.04em]">No requests yet.</p>
            <p className="mx-auto mt-4 max-w-md text-sm leading-6 text-white/42">Tell us about your business and we’ll create your first custom demo before you pay anything.</p>
            <Link href="/start" className="button-primary mt-7"><CirclePlus className="size-4" aria-hidden="true" />Start your first request</Link>
          </div>
        )}
      </section>
    </main>
  );
}
