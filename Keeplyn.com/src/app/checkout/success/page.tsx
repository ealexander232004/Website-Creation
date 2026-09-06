import type { Metadata } from "next";
import Link from "next/link";
import { Check, Clock3 } from "lucide-react";
import { SiteFooter } from "@/components/home-sections";
import { SiteHeader } from "@/components/site-header";
import { getStripe } from "@/lib/stripe";

export const metadata: Metadata = {
  title: "Payment status",
  description: "View the status of a Keeplyn Stripe Checkout payment.",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

type SuccessPageProps = {
  searchParams: Promise<{ session_id?: string | string[] }>;
};

export default async function CheckoutSuccessPage({ searchParams }: SuccessPageProps) {
  const query = await searchParams;
  const sessionId = typeof query.session_id === "string" ? query.session_id : undefined;
  let paymentStatus: "paid" | "processing" | "unverified" = "unverified";

  if (sessionId?.startsWith("cs_")) {
    try {
      const session = await getStripe().checkout.sessions.retrieve(sessionId);

      if (session.metadata?.source === "keeplyn.com") {
        paymentStatus = session.payment_status === "paid" ? "paid" : "processing";
      }
    } catch {
      paymentStatus = "unverified";
    }
  }

  const paid = paymentStatus === "paid";
  const processing = paymentStatus === "processing";

  return (
    <>
      <SiteHeader />
      <main className="flex min-h-[calc(100svh-68px)] items-center bg-[#050505] py-20 text-white">
        <div className="site-container w-full">
          <div className="max-w-4xl border border-white/14 bg-[#08080c]/90 p-8 sm:p-12">
            <span
              className={`flex size-12 items-center justify-center rounded-full ${
                paid ? "bg-[#c9ff3b] text-black" : "bg-[#7568ff]/18 text-[#9d94ff]"
              }`}
            >
              {paid ? (
                <Check className="size-6" aria-hidden="true" />
              ) : (
                <Clock3 className="size-6" aria-hidden="true" />
              )}
            </span>
            <p className="mt-8 text-[10px] font-semibold uppercase tracking-[0.18em] text-[#c9ff3b]">
              Payment status
            </p>
            <h1 className="mt-4 text-[clamp(3.5rem,9vw,7.5rem)] font-semibold leading-[0.82] tracking-[-0.085em]">
              {paid
                ? "Payment received."
                : processing
                  ? "Payment processing."
                  : "We couldn’t verify this payment."}
            </h1>
            <p className="mt-7 max-w-xl text-base leading-7 text-white/52">
              {paid
                ? "Stripe has confirmed your payment. Keeplyn will follow up with the next project step."
                : processing
                  ? "Stripe is still confirming the payment method. We’ll rely on the verified webhook result before treating it as paid."
                  : "No charge status was exposed. Use the return link from Stripe or contact Keeplyn if you need help."}
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Link href="/" className="button-primary">
                Return home
              </Link>
              <Link href="/contact" className="button-secondary">
                Contact Keeplyn
              </Link>
            </div>
          </div>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
