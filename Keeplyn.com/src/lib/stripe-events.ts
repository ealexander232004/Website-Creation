import "server-only";

import type Stripe from "stripe";

const HANDLED_EVENT_TYPES = new Set([
  "checkout.session.completed",
  "checkout.session.async_payment_succeeded",
  "checkout.session.async_payment_failed",
  "invoice.paid",
  "invoice.payment_failed",
  "invoice.voided",
  "charge.refunded",
  "credit_note.created",
]);

export async function processStripeEvent(event: Stripe.Event) {
  if (!HANDLED_EVENT_TYPES.has(event.type)) {
    return { handled: false } as const;
  }

  const object = event.data.object as { id?: string };

  // Keep logs deliberately free of customer details and payment credentials.
  // Add fulfillment or CRM updates here; the webhook ledger guarantees that a
  // completed event ID is not processed again during Stripe delivery retries.
  console.info("Processed Stripe webhook event", {
    eventId: event.id,
    eventType: event.type,
    livemode: event.livemode,
    objectId: object.id,
  });

  return { handled: true } as const;
}
