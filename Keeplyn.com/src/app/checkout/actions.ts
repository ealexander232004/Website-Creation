"use server";

import { randomUUID } from "node:crypto";
import type Stripe from "stripe";
import { redirect } from "next/navigation";
import { getSiteUrl, getStripe } from "@/lib/stripe";
import {
  getStripePlanPrices,
  isWebsitePlanId,
} from "@/lib/stripe-catalog";

const checkoutAttemptPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function createCheckoutSession(formData: FormData) {
  const planValue = formData.get("plan");
  const includeHosting = formData.get("includeHosting") === "on";

  if (!isWebsitePlanId(planValue)) {
    redirect("/pricing");
  }

  const submittedAttemptId = formData.get("checkoutAttemptId");
  const checkoutAttemptId =
    typeof submittedAttemptId === "string" && checkoutAttemptPattern.test(submittedAttemptId)
      ? submittedAttemptId
      : randomUUID();
  const siteUrl = getSiteUrl();
  const prices = getStripePlanPrices(planValue);
  const metadata = {
    plan: planValue,
    hosting: includeHosting ? "included" : "not_included",
    checkout_attempt_id: checkoutAttemptId,
  };
  const lineItems: Stripe.Checkout.SessionCreateParams.LineItem[] = [
    { price: prices.buildPriceId, quantity: 1 },
  ];

  if (includeHosting) {
    lineItems.push({ price: prices.hostingPriceId, quantity: 1 });
  }

  const mode: Stripe.Checkout.SessionCreateParams.Mode = includeHosting
    ? "subscription"
    : "payment";
  const sessionParameters: Stripe.Checkout.SessionCreateParams = {
    mode,
    ui_mode: "hosted_page",
    origin_context: "web",
    line_items: lineItems,
    automatic_tax: {
      enabled: process.env.STRIPE_TAX_ENABLED !== "false",
    },
    billing_address_collection: "required",
    tax_id_collection: { enabled: true },
    allow_promotion_codes: true,
    client_reference_id: checkoutAttemptId,
    metadata,
    success_url: `${siteUrl}/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${siteUrl}/checkout?plan=${planValue}&canceled=1`,
    custom_text: {
      submit: {
        message: "Your receipt or invoice will be emailed after payment.",
      },
    },
  };

  if (mode === "payment") {
    sessionParameters.customer_creation = "always";
    sessionParameters.submit_type = "pay";
    sessionParameters.invoice_creation = {
      enabled: true,
      invoice_data: {
        description: `Keeplyn ${planValue} website build`,
        metadata,
      },
    };
    sessionParameters.payment_intent_data = { metadata };
  } else {
    sessionParameters.submit_type = "subscribe";
    sessionParameters.subscription_data = { metadata };
  }

  let checkoutUrl: string | null = null;

  try {
    const session = await getStripe().checkout.sessions.create(sessionParameters, {
      idempotencyKey: `keeplyn-checkout-${checkoutAttemptId}-${includeHosting ? "with-hosting" : "build-only"}`,
    });
    checkoutUrl = session.url;
  } catch (error) {
    console.error(
      "Unable to create a Stripe Checkout Session.",
      error instanceof Error ? error.message : "Unknown Stripe error",
    );
  }

  if (!checkoutUrl) {
    redirect(`/checkout?plan=${planValue}&error=session`);
  }

  redirect(checkoutUrl);
}
