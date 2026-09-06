import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight, CheckCircle2 } from "lucide-react";
import { SiteFooter } from "@/components/home-sections";
import { SiteHeader } from "@/components/site-header";
import { getStripe } from "@/lib/stripe";

export const metadata: Metadata = {
  title: "Payment received",
  description: "Your Keeplyn checkout is complete.",
};

interface CheckoutSuccessPageProps {
  searchParams: Promise<{ session_id?: string | string[] }>;
}

function formatAmount(amount: number | null, currency: string | null) {
  if (amount === null || !currency) return null;

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency.toUpperCase(),
  }).format(amount / 100);
}

export default async function CheckoutSuccessPage({ searchParams }: CheckoutSuccessPageProps) {
  const query = await searchParams;
  const rawSessionId = Array.isArray(query.session_id) ? query.session_id[0] : query.session_id;

  let checkoutDetails: {
    complete: boolean;
    email: string | null;
    total: string | null;
    plan: string | null;
    hostingIncluded: boolean;
  } | null = null;

  if (rawSessionId?.startsWith("cs_")) {
    try {
      const session = await getStripe().checkout.sessions.retrieve(rawSessionId);
      checkoutDetails = {
        complete: session.status === "complete" && session.payment_status !== "unpaid",
        email: session.customer_details?.email ?? null,
        total: formatAmount(session.amount_total, session.currency),
        plan: session.metadata?.plan ?? null,
        hostingIncluded: session.metadata?.hosting === "included",
      };
    } catch (error) {
      console.error(
        "Unable to verify the Stripe Checkout Session.",
        error instanceof Error ? error.message : "Unknown Stripe error",
      );
    }
  }

  const verified = checkoutDetails?.complete === true;
  const statusMessage = verified && checkoutDetails
    ? `Your ${checkoutDetails.plan ?? "website"} order${checkoutDetails.hostingIncluded ? " with hosting and updates" : ""} is confirmed${checkoutDetails.total ? ` for ${checkoutDetails.total}` : ""}. We’ll follow up with the next project steps${checkoutDetails.email ? ` at ${checkoutDetails.email}` : ""}.`
    : "We could not verify a completed Checkout Session from this link. If Stripe confirmed your payment, your receipt is still the authoritative record.";

  return (
    <>
      <SiteHeader />
      <main className="flex min-h-[calc(100svh-68px)] items-center bg-[#050505] py-20 text-white">
        <div className="site-container w-full">
          <section className="mx-auto max-w-3xl border border-white/14 bg-[#09090d] p-8 text-center shadow-[0_40px_150px_rgba(0,0,0,0.5)] sm:p-14">
            <CheckCircle2 className={`mx-auto size-14 ${verified ? "text-[#c9ff3b]" : "text-white/32"}`} aria-hidden="true" />
            <p className="mt-8 text-[10px] font-semibold uppercase tracking-[0.18em] text-[#c9ff3b]">
              {verified ? "Payment received" : "Checkout status"}
            </p>
            <h1 className="mt-5 text-[clamp(3.5rem,9vw,7rem)] font-semibold leading-[0.82] tracking-[-0.085em]">
              {verified ? "Let’s get to work." : "We’re checking your payment."}
            </h1>
            <p className="mx-auto mt-7 max-w-xl text-sm leading-7 text-white/48 sm:text-base">
              {statusMessage}
            </p>
            <div className="mt-10 flex flex-wrap justify-center gap-3">
              <Link href="/contact" className="button-primary">
                Send project details
                <ArrowUpRight className="size-4" aria-hidden="true" />
              </Link>
              <Link href="/" className="button-secondary">Return home</Link>
            </div>
          </section>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
