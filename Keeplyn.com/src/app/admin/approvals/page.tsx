import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { ArrowLeft, Check, ExternalLink, Inbox, LoaderCircle, Mail, Undo2 } from "lucide-react";
import { approveDemo, approveEmail, approveRevision, rejectItem } from "@/app/admin/approvals/actions";
import { SiteHeader } from "@/components/site-header";
import { formatDate, formatRequestNumber } from "@/lib/customer-lifecycle";
import { opsKindLabels, opsStatusLabels, type OpsItem } from "@/lib/ops";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Approvals" };

const fieldClass = "mt-2 w-full border border-white/14 bg-black/30 px-4 py-3 text-sm leading-6 text-white outline-none focus:border-[#c9ff3b]";

export default async function ApprovalsPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/start?mode=signin");
  const { data: admin } = await supabase.rpc("is_keeplyn_admin");
  if (!admin) redirect("/portal");

  const [{ data: open, error }, { data: recent }] = await Promise.all([
    supabase.from("ops_items").select("*").in("status", ["pending", "working", "approved"]).order("created_at", { ascending: true }),
    supabase.from("ops_items").select("*").in("status", ["sent", "rejected", "failed", "superseded"]).order("updated_at", { ascending: false }).limit(20),
  ]);
  if (error) throw new Error(error.message);
  const items = (open ?? []) as OpsItem[];
  const pending = items.filter((item) => item.status === "pending");
  const inFlight = items.filter((item) => item.status !== "pending");
  const handled = (recent ?? []) as OpsItem[];

  return (
    <main className="min-h-svh bg-[#050505] text-white">
      <SiteHeader />
      <section className="site-container py-10 sm:py-16">
        <Link href="/admin" className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-white/38 hover:text-white"><ArrowLeft className="size-3.5" />Build queue</Link>
        <div className="mt-6 border-b border-white/10 pb-8">
          <p className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9ff3b]"><Inbox className="size-3.5" />Keeplyn operations</p>
          <h1 className="mt-4 text-[clamp(3.25rem,9vw,7rem)] font-semibold leading-[0.82] tracking-[-0.08em]">Approvals.</h1>
          <p className="mt-5 max-w-xl text-sm leading-6 text-white/45">Nothing reaches a customer or lead until you approve it here.</p>
        </div>

        <h2 className="mt-10 text-xs font-semibold uppercase tracking-[0.16em] text-white/45">Waiting for you · {pending.length}</h2>
        <div className="mt-4 space-y-5">
          {pending.map((item) => <PendingCard key={item.id} item={item} />)}
          {!pending.length ? <p className="border border-white/10 px-5 py-12 text-center text-sm text-white/38">You’re all caught up.</p> : null}
        </div>

        {inFlight.length ? <>
          <h2 className="mt-12 text-xs font-semibold uppercase tracking-[0.16em] text-white/45">In progress</h2>
          <ul className="mt-4 divide-y divide-white/10 border border-white/10">{inFlight.map((item) => <StatusRow key={item.id} item={item} />)}</ul>
        </> : null}

        {handled.length ? <>
          <h2 className="mt-12 text-xs font-semibold uppercase tracking-[0.16em] text-white/45">Recently handled</h2>
          <ul className="mt-4 divide-y divide-white/10 border border-white/10">{handled.map((item) => <StatusRow key={item.id} item={item} />)}</ul>
        </> : null}
      </section>
    </main>
  );
}

function PendingCard({ item }: { item: OpsItem }) {
  return (
    <article className="border border-white/12 bg-white/[0.02] p-5 sm:p-7">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] font-semibold uppercase tracking-[0.14em]">
        <span className="text-[#c9ff3b]">{opsKindLabels[item.kind]}</span>
        {item.request_id ? <Link href={`/admin/requests/${item.request_id}`} className="text-white/40 hover:text-white">Request {formatRequestNumber(item.request_id)}</Link> : null}
        <span className="text-white/28">{formatDate(item.created_at)}</span>
      </div>
      <h3 className="mt-3 text-2xl font-semibold tracking-[-0.04em]">{item.title}</h3>
      {item.summary ? <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-white/55">{item.summary}</p> : null}
      {item.kind === "email_reply" ? <EmailReview item={item} /> : <SiteReview item={item} />}
    </article>
  );
}

function SiteReview({ item }: { item: OpsItem }) {
  return (
    <>
      {item.demo_url ? <a href={item.demo_url} target="_blank" rel="noreferrer" className="button-secondary mt-5 !px-4 !py-2.5">Open {item.kind === "revision" ? "preview" : "demo"} <ExternalLink className="size-4" /></a> : null}
      {item.kind === "demo" ? (
        <form action={approveDemo} className="mt-5">
          <input type="hidden" name="itemId" value={item.id} />
          <button className="button-primary w-full sm:w-auto"><Check className="size-4" />Publish & email customer</button>
        </form>
      ) : (
        <form action={approveRevision} className="mt-5">
          <input type="hidden" name="itemId" value={item.id} />
          <label className="block text-xs font-semibold text-white/58">Message to customer
            <textarea name="message" required maxLength={10000} defaultValue={item.draft_body ?? ""} className={`${fieldClass} min-h-32 resize-y`} />
          </label>
          <button className="button-primary mt-4 w-full sm:w-auto"><Check className="size-4" />Approve & email customer</button>
        </form>
      )}
      <RejectForm item={item} label="Send back to the builder" placeholder="What should change?" />
    </>
  );
}

function EmailReview({ item }: { item: OpsItem }) {
  return (
    <>
      <p className="mt-4 flex items-center gap-2 text-xs text-white/45"><Mail className="size-3.5" />To {item.email_to}{item.email_subject ? ` · ${item.email_subject}` : ""}</p>
      {item.inbound_body ? (
        <details className="mt-4 border-l-2 border-white/15 pl-4" open>
          <summary className="cursor-pointer text-xs font-semibold text-white/50">Their message</summary>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-white/55">{item.inbound_body}</p>
        </details>
      ) : null}
      <form action={approveEmail} className="mt-5">
        <input type="hidden" name="itemId" value={item.id} />
        <label className="block text-xs font-semibold text-white/58">Your reply
          <textarea name="body" required maxLength={10000} defaultValue={item.draft_body ?? ""} className={`${fieldClass} min-h-44 resize-y`} />
        </label>
        <button className="button-primary mt-4 w-full sm:w-auto"><Check className="size-4" />Send reply</button>
      </form>
      <RejectForm item={item} label="Discard draft" placeholder="Optional note" />
    </>
  );
}

function RejectForm({ item, label, placeholder }: { item: OpsItem; label: string; placeholder: string }) {
  return (
    <details className="mt-4">
      <summary className="inline-flex cursor-pointer items-center gap-2 text-xs font-semibold text-white/45 hover:text-white"><Undo2 className="size-3.5" />{label}</summary>
      <form action={rejectItem} className="mt-3">
        <input type="hidden" name="itemId" value={item.id} />
        <textarea name="note" maxLength={4000} placeholder={placeholder} className={`${fieldClass} min-h-24 resize-y`} />
        <button className="button-secondary mt-3 !px-4 !py-2.5">{label}</button>
      </form>
    </details>
  );
}

function StatusRow({ item }: { item: OpsItem }) {
  return (
    <li className="flex flex-col gap-1 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
      <span className="text-sm text-white/70"><span className="mr-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-white/35">{opsKindLabels[item.kind]}</span>{item.title}</span>
      <span className={`inline-flex items-center gap-2 text-xs ${item.status === "failed" ? "text-red-300" : "text-white/40"}`}>
        {item.status === "working" || item.status === "approved" ? <LoaderCircle className="size-3.5 animate-spin" /> : null}
        {opsStatusLabels[item.status]}{item.result && item.status === "failed" ? ` — ${item.result}` : ""} · {formatDate(item.updated_at)}
      </span>
    </li>
  );
}
