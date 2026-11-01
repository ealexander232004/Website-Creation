import "server-only";

import { track } from "@vercel/analytics/server";

/**
 * Server-side funnel milestones for Vercel Web Analytics (custom events). The
 * client-side ones live in the /start flow. Tracking must never break the action.
 */
export async function trackFunnel(name: string, properties?: Record<string, string | number | boolean | null>, request?: Request) {
  try {
    await track(name, properties, request ? { request } : undefined);
  } catch (error) {
    console.error("Analytics event failed", name, error);
  }
}
