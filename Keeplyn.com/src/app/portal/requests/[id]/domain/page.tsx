import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { ArrowLeft, ArrowRight, CheckCircle2, CircleDashed, ExternalLink, RefreshCw, ShieldCheck, TriangleAlert } from "lucide-react";
import { SiteHeader } from "@/components/site-header";
import { saveDomain, saveDomainAndCheckout } from "@/app/portal/checkout-actions";
import type { WebsiteRequest } from "@/lib/customer-lifecycle";
import { checkDomain, DNS_TARGETS, type DomainCheck } from "@/lib/domain-check";
import { websitePlans } from "@/lib/plans";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Domain setup" };
type PageProps = { params: Promise<{ id: string }>; searchParams: Promise<{ step?: string; error?: string }> };

const PORKBUN = "https://porkbun.com";

function Step({ number, title, done, children, id }: { number: number; title: string; done?: boolean; children: React.ReactNode; id?: string }) {
  return (
    <section id={id} className="scroll-mt-24 border border-white/12 bg-white/[0.02] p-6 sm:p-8">
      <div className="flex items-center gap-4">
        <span className={`grid size-9 shrink-0 place-items-center rounded-full border text-sm font-semibold ${done ? "border-[#c9ff3b] bg-[#c9ff3b] text-black" : "border-white/20 text-white/70"}`}>
          {done ? <CheckCircle2 className="size-5" aria-label="Done" /> : number}
        </span>
        <h2 className="text-2xl font-semibold tracking-[-0.045em] sm:text-3xl">{title}</h2>
      </div>
      <div className="mt-6 space-y-4 text-sm leading-7 text-white/58">{children}</div>
    </section>
  );
}

function Status({ ok, label, detail }: { ok: boolean; label: string; detail?: string }) {
  return (
    <li className="flex items-start gap-3">
      {ok ? <CheckCircle2 className="mt-1 size-4 shrink-0 text-[#c9ff3b]" aria-hidden="true" /> : <CircleDashed className="mt-1 size-4 shrink-0 text-white/30" aria-hidden="true" />}
      <span>
        <span className={ok ? "text-white/80" : "text-white/50"}>{label}</span>
        <span className="sr-only">{ok ? " (done)" : " (not yet)"}</span>
        {detail ? <span className="block text-xs text-white/34">{detail}</span> : null}
      </span>
    </li>
  );
}

function RecordTable() {
  const rows = [
    { type: "A", host: "(leave blank)", answer: DNS_TARGETS.apexA },
    { type: "CNAME", host: "www", answer: DNS_TARGETS.wwwCname },
  ];
  return (
    <div className="overflow-x-auto border border-white/12">
      <table className="w-full min-w-[30rem] text-left text-sm">
        <thead className="bg-white/[0.04] text-[10px] uppercase tracking-[0.14em] text-white/40">
          <tr>
            <th className="px-4 py-3 font-semibold">Type</th>
            <th className="px-4 py-3 font-semibold">Host</th>
            <th className="px-4 py-3 font-semibold">Answer</th>
            <th className="px-4 py-3 font-semibold">TTL</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.type} className="border-t border-white/10">
              <td className="px-4 py-3 font-semibold text-white">{row.type}</td>
              <td className="px-4 py-3 text-white/70">{row.host}</td>
              <td className="px-4 py-3"><code className="select-all bg-white/[0.06] px-2 py-1 font-mono text-[13px] text-[#c9ff3b]">{row.answer}</code></td>
              <td className="px-4 py-3 text-white/50">600</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ConnectionPanel({ check, requestId }: { check: DomainCheck; requestId: number }) {
  return (
    <div className="border border-white/12 bg-black/30 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="font-semibold text-white">
          {check.ready ? "Connected to Keeplyn" : check.unavailable ? "Couldn’t check right now" : "Not connected yet"}
          <span className="ml-2 font-mono text-xs font-normal text-white/40">{check.domain}</span>
        </p>
        <Link href={`/portal/requests/${requestId}/domain#connect`} className="button-secondary !px-3 !py-2 text-xs">
          <RefreshCw className="size-3.5" aria-hidden="true" />
          Check again
        </Link>
      </div>
      <ul className="mt-4 space-y-3 text-sm">
        <Status ok={check.registered} label="Domain is registered" detail={check.registered ? undefined : "If you just bought it, give it a few minutes."} />
        <Status ok={check.apexConnected} label={`${check.domain} points to Keeplyn`} detail={check.apexConnected ? undefined : check.apexValues.length ? `Currently points to ${check.apexValues.join(", ")}` : "No A record found yet"} />
        <Status ok={check.wwwConnected} label={`www.${check.domain} points to Keeplyn`} detail={check.wwwConnected ? undefined : check.wwwValues.length ? `Currently points to ${check.wwwValues.join(", ")}` : "No www record found yet"} />
      </ul>
      {check.parkingActive ? (
        <p className="mt-4 flex items-start gap-2 border border-[#ffcf5c]/30 bg-[#ffcf5c]/[0.06] px-3 py-2 text-xs leading-5 text-[#ffe19a]">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          Porkbun’s parking page is still active. Delete the default records that point to pixie.porkbun.com or uixie.porkbun.com (step 3).
        </p>
      ) : null}
      {!check.ready && !check.unavailable ? (
        <p className="mt-4 text-xs leading-5 text-white/38">Changes at Porkbun usually show up within 5–15 minutes, occasionally up to an hour. You can leave this page and come back.</p>
      ) : null}
    </div>
  );
}

export default async function DomainSetupPage({ params, searchParams }: PageProps) {
  const [{ id }, query] = await Promise.all([params, searchParams]);
  const requestId = Number(id);
  if (!Number.isInteger(requestId) || requestId < 1) notFound();
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/start?mode=signin");
  const { data, error } = await supabase.from("website_requests").select("*").eq("id", requestId).single();
  if (error || !data) notFound();
  const request = data as WebsiteRequest;
  if (!request.approved_at) redirect(`/portal/requests/${request.id}`);
  const plan = websitePlans.find((item) => item.id === request.plan_id)!;
  const check = request.domain_name ? await checkDomain(request.domain_name) : null;
  // Payment is the last step: it opens after the customer has worked through
  // DNS setup, or if they already reached checkout before.
  const paymentOpen = Boolean(request.domain_name) && (query.step === "pay" || request.payment_status !== "ready");

  return (
    <main className="min-h-svh bg-[#050505] text-white">
      <SiteHeader />
      <section className="site-container py-12 sm:py-20">
        <Link href={`/portal/requests/${request.id}`} className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-white/38 hover:text-white">
          <ArrowLeft className="size-3.5" />
          Request details
        </Link>
        <div className="mt-10 grid gap-10 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9ff3b]">Approved · Final setup</p>
            <h1 className="mt-5 text-[clamp(3.5rem,9vw,7rem)] font-semibold leading-[0.8] tracking-[-0.085em]">Choose your address.</h1>
            <p className="mt-7 max-w-2xl text-sm leading-7 text-white/48">
              Your website is approved. Before payment, we’ll get your domain bought and pointed at Keeplyn, so your site can go live the moment you check out. It takes about 10 minutes and you only do it once.
            </p>

            <div className="mt-10 space-y-5">
              <Step number={1} title="Buy your domain at Porkbun" done={Boolean(check?.registered)}>
                <p>We recommend Porkbun: fair prices, and free privacy protection and security certificates. A .com usually costs about $11 a year.</p>
                <ol className="list-decimal space-y-2 pl-5 marker:text-white/40">
                  <li>
                    Go to{" "}
                    <a href={PORKBUN} target="_blank" rel="noreferrer" className="text-[#c9ff3b] underline decoration-[#c9ff3b]/40 underline-offset-4">
                      porkbun.com <ExternalLink className="inline size-3" aria-hidden="true" />
                    </a>{" "}
                    and search for the name you want, such as <em>yourbusiness</em>.
                  </li>
                  <li>Pick an available name. A <strong className="text-white/80">.com</strong> is easiest for customers to remember; your city or trade works well if the plain name is taken, e.g. <em>yourbusinessportland.com</em>.</li>
                  <li>Click the cart icon next to it, then <strong className="text-white/80">Continue to Checkout</strong>.</li>
                  <li>Skip the add-ons. You don’t need Porkbun’s website builder, hosting, or SSL — Keeplyn provides all of that. WHOIS privacy is free and already included.</li>
                  <li>Create a Porkbun account (or sign in) and pay. Keep auto-renew on so the domain doesn’t expire.</li>
                </ol>
                <p className="text-white/42">Already own a domain somewhere else (GoDaddy, Namecheap, Squarespace…)? Skip to step 2 and add the same records in step 3 at that company instead.</p>
              </Step>

              <Step number={2} title="Tell us your domain" done={Boolean(request.domain_name)}>
                <form action={saveDomain} className="space-y-4">
                  <input type="hidden" name="requestId" value={request.id} />
                  <label className="block text-xs font-semibold text-white/62">
                    Domain you bought
                    <input
                      name="domain"
                      required
                      defaultValue={request.domain_name ?? ""}
                      className="mt-2 w-full border border-white/14 bg-white/[0.045] px-4 py-4 text-lg text-white outline-none focus:border-[#c9ff3b]"
                      placeholder="yourbusiness.com"
                      autoComplete="off"
                      spellCheck={false}
                    />
                  </label>
                  {query.error === "domain" ? <p className="text-sm text-[#ffb4a8]" role="alert">Enter just the domain, like yourbusiness.com.</p> : null}
                  <button className="button-secondary">{request.domain_name ? "Update domain" : "Save domain"}</button>
                </form>
              </Step>

              <Step number={3} title="Point it to Keeplyn" done={Boolean(check?.ready)} id="connect">
                <p>This tells the internet that your domain’s website lives at Keeplyn. In Porkbun:</p>
                <ol className="list-decimal space-y-2 pl-5 marker:text-white/40">
                  <li>Sign in and open <strong className="text-white/80">Account → Domain Management</strong>.</li>
                  <li>Find your domain and click <strong className="text-white/80">DNS</strong> (under its name, or in the <em>Details</em> menu).</li>
                  <li>
                    At the bottom, under <em>Current Records</em>, delete Porkbun’s default parking records: the <strong className="text-white/80">ALIAS</strong> and <strong className="text-white/80">CNAME</strong> records whose answer is <code className="font-mono text-xs text-white/70">pixie.porkbun.com</code> or <code className="font-mono text-xs text-white/70">uixie.porkbun.com</code>. Leave any MX or TXT records alone — those are for email.
                  </li>
                  <li>Add these two records, one at a time, using the form at the top (choose the <em>Type</em>, fill in <em>Host</em> and <em>Answer</em>, then <strong className="text-white/80">Add</strong>):</li>
                </ol>
                <RecordTable />
                <p className="text-white/42">Leaving the Host blank means the record applies to the plain domain (yourbusiness.com). Porkbun fills in the rest of the name for you, so type exactly what’s shown.</p>
                {check ? <ConnectionPanel check={check} requestId={request.id} /> : <p className="text-white/38">Save your domain in step 2 to see its live connection status here.</p>}
                {request.domain_name && !paymentOpen ? (
                  <Link href={`/portal/requests/${request.id}/domain?step=pay#pay`} className="button-primary">
                    I’ve added the records — continue <ArrowRight className="size-4" aria-hidden="true" />
                  </Link>
                ) : null}
              </Step>

              <Step number={4} title="Choose care and pay" done={false} id="pay">
                {!paymentOpen ? (
                  <p className="text-white/38">Finish the steps above, then continue here to review and pay.</p>
                ) : (
                <form action={saveDomainAndCheckout} className="space-y-5">
                  <input type="hidden" name="requestId" value={request.id} />
                  <label className="flex cursor-pointer items-start gap-4 border border-white/14 bg-white/[0.025] p-5">
                    <input type="checkbox" name="hosting" defaultChecked={request.hosting_selected} className="mt-1 size-4 accent-[#c9ff3b]" />
                    <span>
                      <span className="block font-semibold text-white">Add Keeplyn care · {plan.hosting}</span>
                      <span className="mt-2 block text-sm leading-6 text-white/42">Hosting, maintenance, and content updates completed in under two business days.</span>
                    </span>
                  </label>
                  <div className="flex items-start gap-3 border border-[#c9ff3b]/22 bg-[#c9ff3b]/[0.04] p-4 text-xs leading-5 text-white/48">
                    <ShieldCheck className="mt-0.5 size-4 shrink-0 text-[#c9ff3b]" />
                    No card details are collected by Keeplyn. The next page is Stripe’s secure checkout. After payment we connect your domain and launch — usually the same day.
                  </div>
                  {check && !check.ready ? (
                    <p className="text-xs leading-5 text-white/40">Your domain isn’t showing as connected yet — that’s fine if you just added the records. We’ll finish connecting it after payment and email you if anything needs fixing.</p>
                  ) : null}
                  <button className="button-primary">
                    Continue to Stripe <ArrowRight className="size-4" />
                  </button>
                </form>
                )}
              </Step>
            </div>
          </div>

          <aside className="h-fit border border-white/12 bg-white/[0.025] p-6 lg:sticky lg:top-24">
            <p className="text-[10px] uppercase tracking-[0.15em] text-white/28">Approved build</p>
            <p className="mt-3 text-4xl font-semibold tracking-[-0.06em]">{plan.price}</p>
            <p className="mt-3 text-sm text-white/42">One-time {plan.name} website build</p>
            <ol className="mt-7 space-y-3 border-t border-white/10 pt-5 text-sm">
              <Status ok={Boolean(check?.registered)} label="Buy domain" />
              <Status ok={Boolean(request.domain_name)} label="Tell us your domain" />
              <Status ok={Boolean(check?.ready)} label="Point it to Keeplyn" />
              <Status ok={false} label="Pay and launch" />
            </ol>
            <div className="mt-7 border-t border-white/10 pt-5 text-xs leading-5 text-white/34">
              You haven’t been charged for anything yet. Stuck? Email <a className="underline" href="mailto:support@keeplyn.com">support@keeplyn.com</a> and we’ll walk you through it.
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
