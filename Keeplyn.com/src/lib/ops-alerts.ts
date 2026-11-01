import "server-only";

import { createHash } from "node:crypto";
import { opsKindLabels, type OpsItemKind } from "@/lib/ops";

/** Shape returned by public.ops_alert_report(). */
export type OpsAlertReport = {
  worker_seen_at: string | null;
  pending: { id: number; kind: OpsItemKind; title: string; since: string }[];
  failed: { id: number; kind: OpsItemKind; title: string; since: string; error: string | null }[];
  stalled: { id: number; name: string; since: string }[];
  changes: { id: number; name: string; since: string }[];
};

const HOUR = 60 * 60 * 1000;
const WORKER_QUIET_AFTER = 2 * HOUR;
const REMIND_PENDING_AFTER = 4 * HOUR;

const centralTime = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/Chicago",
  weekday: "short",
  hour: "numeric",
  minute: "2-digit",
});

function when(iso: string) {
  return `${centralTime.format(new Date(iso))} CT`;
}

/**
 * Turns the report into an email for support@, or null when nothing needs attention.
 * "event" runs when the worker queues work and lists everything waiting; "watchdog"
 * runs hourly from Vercel and only speaks up about problems or approvals left waiting.
 */
export function buildOpsAlert(report: OpsAlertReport, mode: "event" | "watchdog", approvalsUrl: string, now = Date.now()) {
  const quietSince = report.worker_seen_at && now - Date.parse(report.worker_seen_at) > WORKER_QUIET_AFTER ? report.worker_seen_at : null;
  const pending = mode === "event" ? report.pending : report.pending.filter((item) => now - Date.parse(item.since) > REMIND_PENDING_AFTER);
  const workerDown = mode === "watchdog" && quietSince !== null;
  if (!workerDown && !report.failed.length && !report.stalled.length && !report.changes.length && !pending.length) return null;

  const lines: string[] = [];
  if (workerDown) {
    lines.push(`The PC worker hasn't checked in since ${when(quietSince)}. New demos, revisions and reply drafts are paused until it's running again (log in to the PC, or enable linger).`);
  }
  if (report.failed.length) {
    lines.push("Failed — needs a look:", ...report.failed.map((item) => `• ${opsKindLabels[item.kind] ?? item.kind}: ${item.title} (${when(item.since)})${item.error ? ` — ${item.error}` : ""}`));
  }
  if (report.stalled.length) {
    lines.push("No demo yet after 24 hours (promise is 2 business days):", ...report.stalled.map((request) => `• ${request.name} — request #${request.id}, submitted ${when(request.since)}`));
  }
  if (report.changes.length) {
    lines.push("Customer edited their brief and nothing has picked it up:", ...report.changes.map((request) => `• ${request.name} — request #${request.id}, edited ${when(request.since)}`));
  }
  if (pending.length) {
    lines.push(
      mode === "event" ? "Waiting for your approval:" : "Still waiting for your approval:",
      ...pending.slice(0, 10).map((item) => `• ${opsKindLabels[item.kind] ?? item.kind}: ${item.title}`),
    );
  }
  lines.push(`Review: ${approvalsUrl}`);

  const problems = report.failed.length + report.stalled.length + report.changes.length;
  const subject = workerDown
    ? "Keeplyn worker is offline"
    : problems
      ? `Keeplyn: ${problems} item${problems === 1 ? " needs" : "s need"} attention`
      : `${pending.length} waiting for approval`;

  // Same content → same key, so Resend sends it once; the watchdog repeats at most daily.
  const fingerprint = JSON.stringify([
    workerDown,
    report.failed.map((item) => item.id),
    report.stalled.map((request) => request.id),
    report.changes.map((request) => `${request.id}@${request.since}`),
    pending.map((item) => item.id),
    mode === "watchdog" ? new Date(now).toISOString().slice(0, 10) : "",
  ]);
  const idempotencyKey = `ops-${mode}-${createHash("sha256").update(fingerprint).digest("hex").slice(0, 32)}`;
  return { subject, lines, idempotencyKey };
}
