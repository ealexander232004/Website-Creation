import { NextResponse } from "next/server";
import { createClient as createSupabaseClient } from "@supabase/supabase-js";
import { sendAdminOpsAlert } from "@/lib/email";
import { buildOpsAlert, type OpsAlertReport } from "@/lib/ops-alerts";
import { getEmailOrigin } from "@/lib/site-url";

export const runtime = "nodejs";

/**
 * Called by the ops worker after it queues work or a build fails. The worker
 * authenticates with the Supabase secret key: only that key can run the ops
 * report, so a successful call proves the caller. The email content comes from
 * the database, never from the request.
 */
export async function POST(request: Request) {
  const key = request.headers.get("authorization")?.match(/^Bearer\s+(\S+)$/)?.[1];
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!key || !url) return NextResponse.json({ error: "Unauthorized." }, { status: 401 });

  const supabase = createSupabaseClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data, error } = await supabase.rpc("ops_alert_report");
  if (error || !data) return NextResponse.json({ error: "Unauthorized." }, { status: 401 });

  const alert = buildOpsAlert(data as OpsAlertReport, "event", `${await getEmailOrigin()}/admin/approvals`);
  if (!alert) return new NextResponse(null, { status: 204 });
  try {
    await sendAdminOpsAlert(alert);
  } catch (sendError) {
    console.error("Ops alert failed", sendError);
    return NextResponse.json({ error: "Email delivery failed." }, { status: 502 });
  }
  return new NextResponse(null, { status: 204 });
}
