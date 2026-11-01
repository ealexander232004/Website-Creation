"use client";

import { Analytics, type BeforeSendEvent } from "@vercel/analytics/next";
import { useEffect } from "react";
import { trackEvent } from "@/lib/analytics-client";

// Our own visits to the admin dashboard would drown out real visitor numbers.
function dropAdminPages(event: BeforeSendEvent) {
  return new URL(event.url).pathname.startsWith("/admin") ? null : event;
}

export function SiteAnalytics() {
  // Cold-email links carry utm_source/utm_campaign; count each visit once per tab.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const source = params.get("utm_source");
    if (!source) return;
    const campaign = params.get("utm_campaign");
    try {
      const key = `keeplyn-campaign-${source}-${campaign}`;
      if (sessionStorage.getItem(key)) return;
      sessionStorage.setItem(key, "1");
    } catch {
      // Storage blocked: count it anyway.
    }
    // Pro allows two properties per event.
    trackEvent("Campaign visit", { campaign: campaign ? `${source}/${campaign}` : source, page: window.location.pathname });
  }, []);

  return <Analytics beforeSend={dropAdminPages} />;
}
