import "server-only";

import Stripe from "stripe";

let stripeClient: Stripe | undefined;

function getRequiredEnvironmentVariable(name: string) {
  const value = process.env[name]?.trim();

  if (!value) {
    throw new Error(`Missing required server environment variable: ${name}`);
  }

  return value;
}

export function getStripe() {
  if (stripeClient) {
    return stripeClient;
  }

  const secretKey = getRequiredEnvironmentVariable("STRIPE_SECRET_KEY");
  const testModeOnly = process.env.STRIPE_TEST_MODE_ONLY !== "false";

  if (!/^(sk|rk)_(test|live)_/.test(secretKey)) {
    throw new Error("STRIPE_SECRET_KEY must be a Stripe secret or restricted key.");
  }

  if (testModeOnly && /^(sk|rk)_live_/.test(secretKey)) {
    throw new Error(
      "A live Stripe key was rejected because STRIPE_TEST_MODE_ONLY is enabled.",
    );
  }

  stripeClient = new Stripe(secretKey, {
    appInfo: {
      name: "Keeplyn website",
      version: "0.1.0",
      url: "https://keeplyn.com",
    },
  });

  return stripeClient;
}

export function getStripeWebhookSecret() {
  return getRequiredEnvironmentVariable("STRIPE_WEBHOOK_SECRET");
}

export function getKeeplynSiteUrl() {
  const configuredUrl = getRequiredEnvironmentVariable("KEEPYLN_SITE_URL");
  const url = new URL(configuredUrl);

  if (url.protocol !== "https:" && url.hostname !== "localhost") {
    throw new Error("KEEPYLN_SITE_URL must use HTTPS outside localhost.");
  }

  return url.origin;
}
