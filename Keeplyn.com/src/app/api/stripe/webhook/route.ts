import type Stripe from "stripe";
import { processStripeEvent } from "@/lib/stripe-events";
import {
  claimStripeEvent,
  completeStripeEvent,
  releaseStripeEvent,
} from "@/lib/stripe-webhook-ledger";
import { getStripe, getStripeWebhookSecret } from "@/lib/stripe";

export async function POST(request: Request) {
  const signature = request.headers.get("stripe-signature");

  if (!signature) {
    return Response.json({ error: "Missing Stripe signature." }, { status: 400 });
  }

  let stripe;
  let webhookSecret;

  try {
    stripe = getStripe();
    webhookSecret = getStripeWebhookSecret();
  } catch (error) {
    console.error("Stripe webhook configuration is unavailable", {
      message: error instanceof Error ? error.message : "Unknown configuration error",
    });
    return Response.json({ error: "Webhook configuration unavailable." }, { status: 503 });
  }

  let event: Stripe.Event;

  try {
    const payload = await request.text();
    event = stripe.webhooks.constructEvent(payload, signature, webhookSecret);
  } catch {
    return Response.json({ error: "Invalid Stripe webhook." }, { status: 400 });
  }

  let claim;

  try {
    claim = await claimStripeEvent(event.id);
  } catch (error) {
    console.error("Stripe webhook ledger is unavailable", {
      message: error instanceof Error ? error.message : "Unknown ledger error",
    });
    return Response.json({ error: "Webhook ledger unavailable." }, { status: 503 });
  }

  if (!claim.claimed) {
    if (claim.state === "completed") {
      return Response.json({ received: true, duplicate: true });
    }

    return Response.json(
      { error: "Webhook event is already processing." },
      { status: 409 },
    );
  }

  try {
    const result = await processStripeEvent(event);
    await completeStripeEvent(event.id);
    return Response.json({ received: true, handled: result.handled });
  } catch (error) {
    await releaseStripeEvent(event.id);
    console.error("Stripe webhook processing failed", {
      eventId: event.id,
      eventType: event.type,
      message: error instanceof Error ? error.message : "Unknown processing error",
    });
    return Response.json({ error: "Webhook processing failed." }, { status: 500 });
  }
}
