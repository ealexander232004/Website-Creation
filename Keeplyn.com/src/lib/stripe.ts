import "server-only";
import Stripe from "stripe";

let stripeClient: Stripe | null = null;
export function getStripe() {
  const secretKey = process.env.STRIPE_SECRET_KEY;
  if (!secretKey) throw new Error("STRIPE_SECRET_KEY is not configured.");
  stripeClient ??= new Stripe(secretKey);
  return stripeClient;
}
export const stripeIntegrationIdentifier = "keeplyn_rqvmtzpa";
export function getStripePriceId(plan: "starter" | "pro", hosting: boolean) {
  const build = plan === "starter" ? process.env.STRIPE_STARTER_BUILD_PRICE_ID : process.env.STRIPE_PRO_BUILD_PRICE_ID;
  const care = plan === "starter" ? process.env.STRIPE_STARTER_HOSTING_PRICE_ID : process.env.STRIPE_PRO_HOSTING_PRICE_ID;
  if (!build || (hosting && !care)) throw new Error("Stripe prices are not configured.");
  return { build, care: hosting ? care : null };
}
