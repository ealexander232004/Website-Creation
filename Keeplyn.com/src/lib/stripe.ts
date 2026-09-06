import "server-only";

import Stripe from "stripe";

let stripeClient: Stripe | undefined;

export function getStripe() {
  if (stripeClient) return stripeClient;

  const secretKey = process.env.STRIPE_SECRET_KEY;

  if (!secretKey) {
    throw new Error("STRIPE_SECRET_KEY is not configured.");
  }

  stripeClient = new Stripe(secretKey, {
    apiVersion: "2026-08-26.dahlia",
    appInfo: {
      name: "Keeplyn website",
      version: "1.0.0",
      url: "https://keeplyn.com",
    },
  });

  return stripeClient;
}

export function getSiteUrl() {
  const configuredUrl = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  const fallbackUrl = "http://localhost:3000";

  try {
    return new URL(configuredUrl || fallbackUrl).origin;
  } catch {
    return fallbackUrl;
  }
}
