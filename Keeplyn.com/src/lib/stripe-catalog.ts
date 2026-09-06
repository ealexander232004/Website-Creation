import "server-only";

import type { WebsitePlan } from "@/lib/plans";

export type WebsitePlanId = WebsitePlan["id"];

interface StripePlanPrices {
  buildPriceId: string;
  hostingPriceId: string;
}

const priceEnvironmentVariables: Record<
  WebsitePlanId,
  { build: string; hosting: string }
> = {
  starter: {
    build: "STRIPE_STARTER_PRICE_ID",
    hosting: "STRIPE_STARTER_HOSTING_PRICE_ID",
  },
  pro: {
    build: "STRIPE_PRO_PRICE_ID",
    hosting: "STRIPE_PRO_HOSTING_PRICE_ID",
  },
};

function requireEnvironmentVariable(name: string) {
  const value = process.env[name]?.trim();

  if (!value) {
    throw new Error(`${name} is not configured.`);
  }

  return value;
}

export function isWebsitePlanId(value: unknown): value is WebsitePlanId {
  return value === "starter" || value === "pro";
}

export function getStripePlanPrices(planId: WebsitePlanId): StripePlanPrices {
  const variables = priceEnvironmentVariables[planId];

  return {
    buildPriceId: requireEnvironmentVariable(variables.build),
    hostingPriceId: requireEnvironmentVariable(variables.hosting),
  };
}
