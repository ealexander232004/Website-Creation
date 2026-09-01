import { NextResponse } from "next/server";
import { sendCustomerNotification } from "@/lib/email";
import { getSiteOrigin } from "@/lib/site-url";
import { createClient } from "@/lib/supabase/server";

type RouteContext = { params: Promise<{ id: string }> };

export async function POST(_request: Request, { params }: RouteContext) {
  const requestId = Number((await params).id);
  if (!Number.isInteger(requestId) || requestId < 1) return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  const { data } = await supabase.from("website_requests").select("id, customer_name, customer_email").eq("id", requestId).single();
  if (!data?.customer_email) return NextResponse.json({ error: "Request not found." }, { status: 404 });
  const origin = await getSiteOrigin();
  try {
    await sendCustomerNotification({ kind: "request_received", to: data.customer_email, customerName: data.customer_name, requestId, detailUrl: `${origin}/portal/requests/${requestId}`, idempotencyKey: `request-received-${requestId}` });
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Request confirmation email failed", error);
    return NextResponse.json({ error: "Email delivery failed." }, { status: 502 });
  }
}
