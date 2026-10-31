"use client";

import { Analytics, type BeforeSendEvent } from "@vercel/analytics/next";

// Our own visits to the admin dashboard would drown out real visitor numbers.
function dropAdminPages(event: BeforeSendEvent) {
  return new URL(event.url).pathname.startsWith("/admin") ? null : event;
}

export function SiteAnalytics() {
  return <Analytics beforeSend={dropAdminPages} />;
}
