"use client";

import { track } from "@vercel/analytics";

/**
 * `track()` silently drops events fired before the analytics script has set up
 * `window.va` (e.g. from an effect on first load). Start the same queue the
 * script drains, so early events are kept.
 */
export function trackEvent(name: string, properties?: Parameters<typeof track>[1]) {
  if (typeof window !== "undefined" && !window.va) {
    window.va = (...params) => {
      (window.vaq ??= []).push(params);
    };
  }
  track(name, properties);
}
