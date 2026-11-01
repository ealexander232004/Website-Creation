import { NextResponse } from "next/server";
import { createClient as createSupabaseClient } from "@supabase/supabase-js";
import { sendAdminOpsAlert } from "@/lib/email";
import { buildOpsAlert, type OpsAlertReport } from "@/lib/ops-alerts";
import { getEmailOrigin } from "@/lib/site-url";

export const runtime = "nodejs";

/**
 * Hourly Vercel cron (vercel.json). Runs without the ops PC, so it also catches
 * a worker that is off. Vercel sends `Authorization: Bearer $CRON_SECRET`; the
 * same secret is the only credential the database accepts for the report.
 */
export async function GET(request: Request) {
  const secret = process.env.CRON_SECRET;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!secret || !url || !publishableKey || request.headers.get("authorization") !== `Bearer ${secret}`) {
    return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
  }

  const supabase = createSupabaseClient(url, publishableKey, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data, error } = await supabase.rpc("ops_watchdog_report", { p_token: secret });
  if (error || !data) {
    console.error("Ops watchdog report failed", error);
    return NextResponse.json({ error: "Report unavailable." }, { status: 502 });
  }

  const alert = buildOpsAlert(data as OpsAlertReport, "watchdog", `${await getEmailOrigin()}/admin/approvals`);
  if (!alert) return NextResponse.json({ ok: true, alerted: false });
  try {
    await sendAdminOpsAlert(alert);
  } catch (sendError) {
    console.error("Ops watchdog alert failed", sendError);
    return NextResponse.json({ error: "Email delivery failed." }, { status: 502 });
  }
  return NextResponse.json({ ok: true, alerted: true });
}
