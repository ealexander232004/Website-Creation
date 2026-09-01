import { NextResponse } from "next/server";
import { createClient as createSupabaseClient } from "@supabase/supabase-js";
import type Stripe from "stripe";
import { getStripe } from "@/lib/stripe";

export const runtime = "nodejs";

function objectId(value: string | { id: string } | null | undefined) {
  return typeof value === "string" ? value : value?.id ?? null;
}

function invoiceSubscription(invoice: Stripe.Invoice) {
  const current = invoice as unknown as {
    subscription?: string | { id: string } | null;
    parent?: { subscription_details?: { subscription?: string | { id: string } | null } | null } | null;
  };
  return objectId(current.subscription ?? current.parent?.subscription_details?.subscription);
}

export async function POST(request: Request) {
  const signature = request.headers.get("stripe-signature");
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  const databaseSecret = process.env.DATABASE_WEBHOOK_SECRET;
  if (!signature || !webhookSecret || !databaseSecret) return NextResponse.json({ error: "Webhook is not configured." }, { status: 503 });

  let event: Stripe.Event;
  try {
    event = getStripe().webhooks.constructEvent(await request.text(), signature, webhookSecret);
  } catch (error) {
    console.error("Stripe signature verification failed", error);
    return NextResponse.json({ error: "Invalid signature." }, { status: 400 });
  }

  let requestId: number | null = null;
  let checkoutSessionId: string | null = null;
  let customerId: string | null = null;
  let subscriptionId: string | null = null;
  let paymentStatus: string | null = null;
  let subscriptionStatus: string | null = null;

  if (event.type.startsWith("checkout.session.")) {
    const session = event.data.object as Stripe.Checkout.Session;
    requestId = Number(session.metadata?.request_id) || null;
    checkoutSessionId = session.id;
    customerId = objectId(session.customer);
    subscriptionId = objectId(session.subscription);
    paymentStatus = session.payment_status;
  } else if (event.type.startsWith("customer.subscription.")) {
    const subscription = event.data.object as Stripe.Subscription;
    requestId = Number(subscription.metadata.request_id) || null;
    customerId = objectId(subscription.customer);
    subscriptionId = subscription.id;
    subscriptionStatus = subscription.status;
  } else if (event.type.startsWith("invoice.")) {
    const invoice = event.data.object as Stripe.Invoice;
    subscriptionId = invoiceSubscription(invoice);
    customerId = objectId(invoice.customer);
  }

  const supabase = createSupabaseClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    { auth: { persistSession: false, autoRefreshToken: false } },
  );
  const { error } = await supabase.rpc("record_stripe_event", {
    p_secret: databaseSecret,
    p_event_id: event.id,
    p_event_type: event.type,
    p_request_id: requestId,
    p_checkout_session_id: checkoutSessionId,
    p_customer_id: customerId,
    p_subscription_id: subscriptionId,
    p_payment_status: paymentStatus,
    p_subscription_status: subscriptionStatus,
  });
  if (error) {
    console.error("Stripe event persistence failed", { eventId: event.id, type: event.type, message: error.message });
    return NextResponse.json({ error: "Event processing failed." }, { status: 500 });
  }
  return NextResponse.json({ received: true });
}
