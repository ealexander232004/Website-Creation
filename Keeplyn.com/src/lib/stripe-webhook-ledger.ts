import "server-only";

import { Redis } from "@upstash/redis";

const PROCESSING_TTL_SECONDS = 5 * 60;
const COMPLETED_TTL_SECONDS = 30 * 24 * 60 * 60;
const KEY_PREFIX = "keeplyn:stripe:webhook:";

type LedgerState = "processing" | "completed";

export type EventClaim =
  | { claimed: true; eventId: string }
  | { claimed: false; state: LedgerState };

type MemoryEntry = {
  state: LedgerState;
  expiresAt: number;
};

const globalLedger = globalThis as typeof globalThis & {
  keeplynStripeWebhookLedger?: Map<string, MemoryEntry>;
};

function getMemoryLedger() {
  globalLedger.keeplynStripeWebhookLedger ??= new Map<string, MemoryEntry>();
  return globalLedger.keeplynStripeWebhookLedger;
}

let redisClient: Redis | undefined;

function getRedis() {
  const url = process.env.UPSTASH_REDIS_REST_URL?.trim();
  const token = process.env.UPSTASH_REDIS_REST_TOKEN?.trim();

  if (Boolean(url) !== Boolean(token)) {
    throw new Error(
      "Both UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN must be configured together.",
    );
  }

  if (!url || !token) {
    if (process.env.NODE_ENV === "production") {
      throw new Error(
        "Durable Stripe webhook idempotency requires the Upstash Redis environment variables in production.",
      );
    }

    return undefined;
  }

  redisClient ??= new Redis({ url, token });
  return redisClient;
}

function eventKey(eventId: string) {
  return `${KEY_PREFIX}${eventId}`;
}

export async function claimStripeEvent(eventId: string): Promise<EventClaim> {
  const redis = getRedis();

  if (redis) {
    const result = await redis.set(eventKey(eventId), "processing", {
      ex: PROCESSING_TTL_SECONDS,
      nx: true,
    });

    if (result === "OK") {
      return { claimed: true, eventId };
    }

    const state = await redis.get<LedgerState>(eventKey(eventId));
    return { claimed: false, state: state ?? "processing" };
  }

  const ledger = getMemoryLedger();
  const now = Date.now();
  const existing = ledger.get(eventId);

  if (existing && existing.expiresAt > now) {
    return { claimed: false, state: existing.state };
  }

  ledger.set(eventId, {
    state: "processing",
    expiresAt: now + PROCESSING_TTL_SECONDS * 1000,
  });

  return { claimed: true, eventId };
}

export async function completeStripeEvent(eventId: string) {
  const redis = getRedis();

  if (redis) {
    await redis.set(eventKey(eventId), "completed", {
      ex: COMPLETED_TTL_SECONDS,
    });
    return;
  }

  getMemoryLedger().set(eventId, {
    state: "completed",
    expiresAt: Date.now() + COMPLETED_TTL_SECONDS * 1000,
  });
}

export async function releaseStripeEvent(eventId: string) {
  const redis = getRedis();

  if (redis) {
    await redis.del(eventKey(eventId));
    return;
  }

  getMemoryLedger().delete(eventId);
}
