import "server-only";
import { headers } from "next/headers";

const PRODUCTION_ORIGIN = `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL || "keeplyn.com"}`;

/** Origin of the current request — use for redirects that must return to this deployment (Stripe, auth). */
export async function getSiteOrigin() {
  const headerStore = await headers();
  const host = headerStore.get("x-forwarded-host") || headerStore.get("host");
  const protocol = headerStore.get("x-forwarded-proto") || (host?.includes("localhost") ? "http" : "https");
  return host ? `${protocol}://${host}` : PRODUCTION_ORIGIN;
}

/**
 * Origin for links in emails. Production always uses the canonical domain, so a link never
 * depends on which host (www, a vercel.app alias) the admin or webhook request came through.
 */
export async function getEmailOrigin() {
  return process.env.VERCEL_ENV === "production" ? PRODUCTION_ORIGIN : getSiteOrigin();
}
