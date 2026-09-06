import type Stripe from "stripe";
import { getStripe } from "@/lib/stripe";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const signature = request.headers.get("stripe-signature");
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!signature || !webhookSecret) {
    return Response.json(
      { error: "Stripe webhook verification is not configured." },
      { status: 503 },
    );
  }

  let event: Stripe.Event;

  try {
    const payload = await request.text();
    event = getStripe().webhooks.constructEvent(payload, signature, webhookSecret);
  } catch (error) {
    console.error(
      "Stripe webhook signature verification failed.",
      error instanceof Error ? error.message : "Unknown verification error",
    );
    return Response.json({ error: "Invalid webhook signature." }, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed":
    case "checkout.session.async_payment_succeeded":
    case "invoice.paid":
    case "invoice.payment_failed":
      console.info("Received Stripe event", event.type, event.id);
      break;
    default:
      break;
  }

  return Response.json({ received: true });
}
