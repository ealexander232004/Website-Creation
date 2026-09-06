import { randomUUID } from "node:crypto";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, ArrowUpRight, Check, LockKeyhole } from "lucide-react";
import { SiteFooter } from "@/components/home-sections";
import { SiteHeader } from "@/components/site-header";
import { websitePlans } from "@/lib/plans";
import { isWebsitePlanId } from "@/lib/stripe-catalog";
import { createCheckoutSession } from "./actions";

export const metadata: Metadata = {
  title: "Checkout",
  description: "Choose a Keeplyn website plan and continue to secure Stripe Checkout.",
};

interface CheckoutPageProps {
  searchParams: Promise<{
    plan?: string | string[];
    canceled?: string | string[];
    error?: string | string[];
  }>;
}

function firstValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function CheckoutPage({ searchParams }: CheckoutPageProps) {
  const query = await searchParams;
  const requestedPlan = firstValue(query.plan);
  const selectedPlanId = isWebsitePlanId(requestedPlan) ? requestedPlan : "starter";
  const selectedPlan = websitePlans.find((plan) => plan.id === selectedPlanId) ?? websitePlans[0];
  const canceled = firstValue(query.canceled) === "1";
  const sessionError = firstValue(query.error) === "session";

  return (
    <>
      <SiteHeader />
      <main className="min-h-[calc(100svh-68px)] bg-[#050505] py-16 text-white sm:py-24">
        <div className="site-container">
          <Link
            href="/pricing"
            className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-white/42 transition-colors hover:text-[#c9ff3b]"
          >
            <ArrowLeft className="size-4" aria-hidden="true" />
            Back to pricing
          </Link>

          <div className="mt-10 grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(22rem,31rem)] lg:items-start">
            <section>
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#c9ff3b]">
                Secure checkout
              </p>
              <h1 className="mt-5 max-w-4xl text-[clamp(4rem,9vw,8rem)] font-semibold leading-[0.78] tracking-[-0.09em]">
                Choose your build.
              </h1>
              <p className="mt-8 max-w-xl text-base leading-7 text-white/48">
                Select a website package, add ongoing hosting if you want it, then review the final total and taxes on Stripe.
              </p>

              <div className="mt-12 grid max-w-3xl gap-3 sm:grid-cols-2">
                {websitePlans.map((plan) => {
                  const selected = plan.id === selectedPlan.id;

                  return (
                    <Link
                      key={plan.id}
                      href={`/checkout?plan=${plan.id}`}
                      aria-current={selected ? "page" : undefined}
                      className={`border p-6 transition-colors ${
                        selected
                          ? "border-[#c9ff3b] bg-[#c9ff3b]/8"
                          : "border-white/14 bg-white/[0.02] hover:border-white/35"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-white/62">{plan.name}</p>
                          <p className="mt-3 text-3xl font-semibold tracking-[-0.06em]">{plan.price}</p>
                        </div>
                        <span className={`grid size-7 place-items-center rounded-full border ${selected ? "border-[#c9ff3b] text-[#c9ff3b]" : "border-white/18 text-transparent"}`}>
                          <Check className="size-4" aria-hidden="true" />
                        </span>
                      </div>
                      <p className="mt-5 text-sm leading-6 text-white/42">{plan.summary}</p>
                    </Link>
                  );
                })}
              </div>
            </section>

            <aside className="border border-white/14 bg-[#09090d] p-6 shadow-[0_35px_120px_rgba(0,0,0,0.45)] sm:p-8 lg:sticky lg:top-24">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/38">Order summary</p>
              <div className="mt-7 flex items-start justify-between gap-5 border-b border-white/12 pb-7">
                <div>
                  <p className="text-xl font-semibold">{selectedPlan.name} website</p>
                  <p className="mt-2 text-xs text-white/38">One-time website build</p>
                </div>
                <p className="text-xl font-semibold">{selectedPlan.price}</p>
              </div>

              {canceled ? (
                <p className="mt-5 border border-[#c9ff3b]/30 bg-[#c9ff3b]/8 px-4 py-3 text-sm text-[#dfff83]">
                  Checkout was canceled. Nothing was charged.
                </p>
              ) : null}
              {sessionError ? (
                <p className="mt-5 border border-red-300/25 bg-red-300/8 px-4 py-3 text-sm text-red-100">
                  Stripe Checkout could not start. Please try again or email hello@keeplyn.com.
                </p>
              ) : null}

              <form action={createCheckoutSession} className="mt-7">
                <input type="hidden" name="plan" value={selectedPlan.id} />
                <input type="hidden" name="checkoutAttemptId" value={randomUUID()} />
                <label className="flex cursor-pointer items-start gap-4 border border-white/12 bg-white/[0.025] p-4 transition-colors hover:border-white/28">
                  <input
                    type="checkbox"
                    name="includeHosting"
                    className="mt-1 size-4 accent-[#c9ff3b]"
                  />
                  <span className="flex-1">
                    <span className="flex items-start justify-between gap-4 font-semibold">
                      Hosting &amp; updates
                      <span className="whitespace-nowrap text-[#c9ff3b]">{selectedPlan.hosting}</span>
                    </span>
                    <span className="mt-2 block text-xs leading-5 text-white/40">
                      Secure hosting plus ongoing content updates. Cancel under the terms of the billing policy.
                    </span>
                  </span>
                </label>

                <button
                  type="submit"
                  className="group mt-5 flex w-full items-center justify-center gap-3 bg-[#c9ff3b] px-5 py-4 text-sm font-semibold text-black transition-colors hover:bg-[#d8ff77]"
                >
                  Continue to Stripe
                  <ArrowUpRight className="size-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" aria-hidden="true" />
                </button>
              </form>

              <div className="mt-5 flex items-center justify-center gap-2 text-[11px] text-white/36">
                <LockKeyhole className="size-3.5" aria-hidden="true" />
                Payment details are handled securely by Stripe
              </div>
              <p className="mt-6 text-center text-[10px] leading-5 text-white/28">
                By continuing, you agree to Keeplyn&apos;s{" "}
                <Link href="/terms-of-service" className="underline underline-offset-2 hover:text-white">terms</Link>
                {" "}and{" "}
                <Link href="/billing-cancellation-policy" className="underline underline-offset-2 hover:text-white">billing policy</Link>.
                Taxes are calculated at checkout.
              </p>
            </aside>
          </div>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
