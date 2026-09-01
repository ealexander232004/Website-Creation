"use server";

import { redirect } from "next/navigation";
import { z } from "zod";
import type { SupabaseClient } from "@supabase/supabase-js";
import type { WebsiteRequest } from "@/lib/customer-lifecycle";
import { getSiteOrigin } from "@/lib/site-url";
import { createClient } from "@/lib/supabase/server";
import { getStripe, getStripePriceId, stripeIntegrationIdentifier } from "@/lib/stripe";

const requestIdSchema = z.coerce.number().int().positive();
const domainSchema = z.string().trim().toLowerCase()
  .transform((value) => value.replace(/^https?:\/\//, "").replace(/^www\./, "").split("/")[0])
  .pipe(z.string().regex(/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/).max(253));

async function requireCheckoutRequest(requestId: number) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/start?mode=signin");
  const { data, error } = await supabase.from("website_requests").select("*").eq("id", requestId).single();
  if (error || !data) throw new Error("Website request not found.");
  return { supabase, request: data as WebsiteRequest };
}

async function checkout(request: WebsiteRequest, supabase: SupabaseClient) {
  const stripe = getStripe();
  if (request.payment_status === "pending" && request.stripe_checkout_session_id) {
    const existing = await stripe.checkout.sessions.retrieve(request.stripe_checkout_session_id);
    if (existing.status === "open" && existing.url) redirect(existing.url);
  }
  if (!request.domain_name || !request.approved_at) throw new Error("Approve the website and add a domain before checkout.");
  const origin = await getSiteOrigin();
  const prices = getStripePriceId(request.plan_id, request.hosting_selected);
  const metadata = { request_id: String(request.id), plan_id: request.plan_id, domain_name: request.domain_name };
  const common = {
    client_reference_id: String(request.id),
    customer_email: request.customer_email || undefined,
    line_items: [{ price: prices.build, quantity: 1 }, ...(prices.care ? [{ price: prices.care, quantity: 1 }] : [])],
    metadata,
    integration_identifier: stripeIntegrationIdentifier,
    success_url: `${origin}/portal/requests/${request.id}?payment=success`,
    cancel_url: `${origin}/portal/requests/${request.id}/domain?payment=cancelled`,
  };
  const session = request.hosting_selected
    ? await stripe.checkout.sessions.create({ ...common, mode: "subscription", subscription_data: { metadata } }, { idempotencyKey: `request-${request.id}-domain-${request.domain_name}-hosting` })
    : await stripe.checkout.sessions.create({ ...common, mode: "payment", customer_creation: "always", payment_intent_data: { metadata } }, { idempotencyKey: `request-${request.id}-domain-${request.domain_name}-build` });
  const { error } = await supabase.rpc("begin_request_checkout", {
    p_request_id: request.id,
    p_checkout_session_id: session.id,
    p_customer_id: typeof session.customer === "string" ? session.customer : null,
  });
  if (error) {
    await stripe.checkout.sessions.expire(session.id);
    throw new Error(error.message);
  }
  if (!session.url) throw new Error("Stripe did not return a checkout URL.");
  redirect(session.url);
}

export async function saveDomainAndCheckout(formData: FormData) {
  const requestId = requestIdSchema.parse(formData.get("requestId"));
  const domain = domainSchema.parse(formData.get("domain"));
  const hostingSelected = formData.get("hosting") === "on";
  const { supabase } = await requireCheckoutRequest(requestId);
  const { error } = await supabase.rpc("set_request_domain", { p_request_id: requestId, p_domain_name: domain, p_hosting_selected: hostingSelected });
  if (error) throw new Error(error.message);
  const { data, error: reloadError } = await supabase.from("website_requests").select("*").eq("id", requestId).single();
  if (reloadError || !data) throw new Error("Could not reload the website request.");
  await checkout(data as WebsiteRequest, supabase);
}

export async function startCheckout(formData: FormData) {
  const requestId = requestIdSchema.parse(formData.get("requestId"));
  const { supabase, request } = await requireCheckoutRequest(requestId);
  await checkout(request, supabase);
}
