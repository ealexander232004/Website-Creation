import { randomUUID } from "node:crypto";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight, Check } from "lucide-react";
import { SiteFooter } from "@/components/home-sections";
import { SiteHeader } from "@/components/site-header";
import { websitePlans } from "@/lib/plans";
import { beginCheckout } from "./actions";

export const metadata: Metadata = {
  title: "Secure checkout",
  description: "Pay for an approved Keeplyn website build through Stripe Checkout.",
  robots: { index: false, follow: false },
};

type CheckoutPageProps = {
  searchParams: Promise<{
    plan?: string | string[];
    status?: string | string[];
  }>;
};

const statusMessages: Record<string, string> = {
  cancelled: "Checkout was cancelled. Nothing was charged.",
  invalid: "That checkout request was invalid. Please choose a plan below.",
  unavailable:
    "Secure checkout is temporarily unavailable. Please try again or contact us.",
};

export default async function CheckoutPage({ searchParams }: CheckoutPageProps) {
  const query = await searchParams;
  const selectedPlan = typeof query.plan === "string" ? query.plan : undefined;
  const status = typeof query.status === "string" ? query.status : undefined;

  return (
    <>
      <SiteHeader />
      <main className="min-h-[calc(100svh-68px)] bg-[#050505] py-20 text-white sm:py-28">
        <div className="site-container">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#c9ff3b]">
            Stripe secure checkout
          </p>
          <h1 className="mt-5 max-w-5xl text-[clamp(4rem,10vw,9rem)] font-semibold leading-[0.78] tracking-[-0.09em]">
            Finish your build.
          </h1>
          <p className="mt-8 max-w-xl text-base leading-7 text-white/52">
            Choose the website build you approved. Stripe securely collects your
            payment details, billing address, and any applicable tax.
          </p>

          {status && statusMessages[status] ? (
            <p
              className="mt-8 max-w-xl border border-white/14 bg-white/[0.035] px-5 py-4 text-sm text-white/72"
              role="status"
            >
              {statusMessages[status]}
            </p>
          ) : null}

          <div className="mt-14 grid max-w-5xl gap-4 md:grid-cols-2">
            {websitePlans.map((plan) => {
              const selected = plan.id === selectedPlan;

              return (
                <article
                  key={plan.id}
                  className={`flex min-h-[28rem] flex-col border p-7 sm:p-9 ${
                    selected
                      ? "border-[#c9ff3b]/70 bg-[#c9ff3b]/[0.045]"
                      : "border-white/14 bg-[#08080c]/88"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h2 className="text-5xl font-semibold tracking-[-0.075em] sm:text-6xl">
                        {plan.name}
                      </h2>
                      <p className="mt-5 max-w-sm text-sm leading-6 text-white/48">
                        {plan.summary}
                      </p>
                    </div>
                    {selected ? (
                      <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-[#c9ff3b] text-black">
                        <Check className="size-4" aria-hidden="true" />
                        <span className="sr-only">Selected plan</span>
                      </span>
                    ) : null}
                  </div>

                  <div className="mt-auto pt-14">
                    <p className="text-5xl font-semibold tracking-[-0.075em] sm:text-6xl">
                      {plan.price}
                    </p>
                    <p className="mt-3 text-xs leading-5 text-white/42">
                      One-time website build. Tax, if applicable, is calculated at
                      checkout. Optional hosting is separate.
                    </p>
                    <form action={beginCheckout} className="mt-7">
                      <input type="hidden" name="planId" value={plan.id} />
                      <input type="hidden" name="requestId" value={randomUUID()} />
                      <button
                        type="submit"
                        className="group flex min-h-14 w-full items-center justify-center gap-2 bg-[#c9ff3b] px-5 text-sm font-semibold text-black transition-colors hover:bg-[#d5ff69]"
                      >
                        Continue to Stripe
                        <ArrowUpRight
                          className="size-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5"
                          aria-hidden="true"
                        />
                      </button>
                    </form>
                  </div>
                </article>
              );
            })}
          </div>

          <p className="mt-8 max-w-2xl text-sm leading-6 text-white/44">
            Need a custom scope or balance invoice instead?{" "}
            <Link href="/contact" className="text-white underline underline-offset-4 hover:text-[#c9ff3b]">
              Contact Keeplyn
            </Link>{" "}
            and we&apos;ll send a Stripe-hosted invoice with itemized terms.
          </p>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
