import { NextResponse } from "next/server";
import { createClient as createSupabaseClient } from "@supabase/supabase-js";
import { sendAdminApprovalsAlert } from "@/lib/email";
import { opsKindLabels, type OpsItemKind } from "@/lib/ops";
import { getEmailOrigin } from "@/lib/site-url";

export const runtime = "nodejs";

/**
 * Called by the ops worker after it queues work for approval. The worker
 * authenticates with the Supabase secret key: only that key can read the
 * queue, so a successful read proves the caller. The email content comes from
 * the database, never from the request.
 */
export async function POST(request: Request) {
  const key = request.headers.get("authorization")?.match(/^Bearer\s+(\S+)$/)?.[1];
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!key || !url) return NextResponse.json({ error: "Unauthorized." }, { status: 401 });

  const supabase = createSupabaseClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data, error } = await supabase
    .from("ops_items")
    .select("id, kind, title")
    .eq("status", "pending")
    .order("id", { ascending: false })
    .limit(25);
  if (error) return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
  if (!data.length) return new NextResponse(null, { status: 204 });

  const origin = await getEmailOrigin();
  try {
    await sendAdminApprovalsAlert({
      items: data.map((item) => ({ kind: opsKindLabels[item.kind as OpsItemKind] ?? item.kind, title: item.title })),
      approvalsUrl: `${origin}/admin/approvals`,
      idempotencyKey: `ops-pending-${data[0].id}-${data.length}`,
    });
  } catch (sendError) {
    console.error("Approvals alert failed", sendError);
    return NextResponse.json({ error: "Email delivery failed." }, { status: 502 });
  }
  return new NextResponse(null, { status: 204 });
}
