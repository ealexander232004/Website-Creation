"use server";

import { redirect } from "next/navigation";
import { getKeeplynSiteUrl, getStripe } from "@/lib/stripe";
import { websitePlans } from "@/lib/plans";

const REQUEST_ID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function beginCheckout(formData: FormData) {
  const planId = formData.get("planId");
  const requestId = formData.get("requestId");
  const plan = websitePlans.find((candidate) => candidate.id === planId);

  if (!plan || typeof requestId !== "string" || !REQUEST_ID_PATTERN.test(requestId)) {
    redirect("/checkout?status=invalid");
  }

  let checkoutUrl: string | null = null;

  try {
    const siteUrl = getKeeplynSiteUrl();
    const serviceTaxCode = process.env.STRIPE_WEBSITE_SERVICE_TAX_CODE?.trim();
    const session = await getStripe().checkout.sessions.create(
      {
        mode: "payment",
        line_items: [
          {
            quantity: 1,
            price_data: {
              currency: "usd",
              unit_amount: plan.amount,
              tax_behavior: "exclusive",
              product_data: {
                name: `Keeplyn ${plan.name} website build`,
                description: plan.summary,
                ...(serviceTaxCode ? { tax_code: serviceTaxCode } : {}),
              },
            },
          },
        ],
        automatic_tax: { enabled: true },
        billing_address_collection: "required",
        customer_creation: "always",
        tax_id_collection: { enabled: true },
        metadata: {
          source: "keeplyn.com",
          plan_id: plan.id,
          checkout_request_id: requestId,
        },
        payment_intent_data: {
          metadata: {
            source: "keeplyn.com",
            plan_id: plan.id,
            checkout_request_id: requestId,
          },
        },
        custom_text: {
          submit: {
            message:
              "This payment covers the website build. Optional hosting and updates are billed separately after approval.",
          },
        },
        success_url: `${siteUrl}/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${siteUrl}/checkout?plan=${plan.id}&status=cancelled`,
      },
      {
        idempotencyKey: `keeplyn-checkout-${plan.id}-${requestId}`,
      },
    );

    checkoutUrl = session.url;
  } catch (error) {
    console.error("Unable to create Stripe Checkout Session", {
      message: error instanceof Error ? error.message : "Unknown Stripe error",
      planId: plan.id,
    });
  }

  if (!checkoutUrl) {
    redirect(`/checkout?plan=${plan.id}&status=unavailable`);
  }

  redirect(checkoutUrl);
}
