"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";
import { sendCustomerNotification } from "@/lib/email";
import { getSiteOrigin } from "@/lib/site-url";
import { createClient } from "@/lib/supabase/server";

const idSchema = z.coerce.number().int().positive();
const httpsUrl = z.string().trim().url().refine((value) => value.startsWith("https://"), "Use a secure URL.");

async function requireAdmin() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/start?mode=signin");
  const { data } = await supabase.rpc("is_keeplyn_admin");
  if (!data) redirect("/portal");
  return supabase;
}

async function getRequestForEmail(supabase: Awaited<ReturnType<typeof createClient>>, requestId: number) {
  const { data, error } = await supabase.from("website_requests").select("id, customer_name, customer_email, demo_url, live_url, updated_at").eq("id", requestId).single();
  if (error || !data?.customer_email) throw new Error("Customer email is unavailable.");
  return data;
}

export async function publishDemo(formData: FormData) {
  const requestId = idSchema.parse(formData.get("requestId"));
  const demoUrl = httpsUrl.parse(formData.get("demoUrl"));
  const supabase = await requireAdmin();
  const { error } = await supabase.rpc("admin_set_demo", { p_request_id: requestId, p_demo_url: demoUrl });
  if (error) throw new Error(error.message);
  const request = await getRequestForEmail(supabase, requestId);
  const origin = await getSiteOrigin();
  await sendCustomerNotification({ kind: "demo_ready", to: request.customer_email, customerName: request.customer_name, requestId, detailUrl: `${origin}/portal/requests/${requestId}`, demoUrl, idempotencyKey: `demo-ready-${requestId}-${encodeURIComponent(demoUrl).slice(-40)}` });
  revalidatePath(`/admin/requests/${requestId}`);
  revalidatePath(`/portal/requests/${requestId}`);
}

export async function setProductionStatus(formData: FormData) {
  const requestId = idSchema.parse(formData.get("requestId"));
  const status = z.enum(["in_review", "in_progress", "launching"]).parse(formData.get("status"));
  const supabase = await requireAdmin();
  const { error } = await supabase.rpc("admin_set_request_status", { p_request_id: requestId, p_status: status, p_live_url: null });
  if (error) throw new Error(error.message);
  revalidatePath(`/admin/requests/${requestId}`);
  revalidatePath(`/portal/requests/${requestId}`);
}

export async function updateTicket(formData: FormData) {
  const ticketId = idSchema.parse(formData.get("ticketId"));
  const status = z.enum(["in_progress", "completed"]).parse(formData.get("status"));
  const response = z.string().trim().max(5000).parse(formData.get("response") ?? "");
  const supabase = await requireAdmin();
  const { data: requestId, error } = await supabase.rpc("admin_set_update_ticket", { p_ticket_id: ticketId, p_status: status, p_admin_response: response || null });
  if (error || !requestId) throw new Error(error?.message || "Update ticket was not found.");
  if (status === "completed") {
    const request = await getRequestForEmail(supabase, Number(requestId));
    const origin = await getSiteOrigin();
    await sendCustomerNotification({ kind: "update_complete", to: request.customer_email, customerName: request.customer_name, requestId: Number(requestId), detailUrl: `${origin}/portal/requests/${requestId}`, demoUrl: request.demo_url, message: response || null, idempotencyKey: `update-complete-${ticketId}` });
  }
  revalidatePath(`/admin/requests/${requestId}`);
  revalidatePath(`/portal/requests/${requestId}`);
}

export async function markWebsiteLive(formData: FormData) {
  const requestId = idSchema.parse(formData.get("requestId"));
  const liveUrl = httpsUrl.parse(formData.get("liveUrl"));
  const supabase = await requireAdmin();
  const { error } = await supabase.rpc("admin_set_request_status", { p_request_id: requestId, p_status: "live", p_live_url: liveUrl });
  if (error) throw new Error(error.message);
  const request = await getRequestForEmail(supabase, requestId);
  const origin = await getSiteOrigin();
  await sendCustomerNotification({ kind: "website_live", to: request.customer_email, customerName: request.customer_name, requestId, detailUrl: `${origin}/portal/requests/${requestId}`, liveUrl, idempotencyKey: `website-live-${requestId}` });
  revalidatePath(`/admin/requests/${requestId}`);
  revalidatePath(`/portal/requests/${requestId}`);
}
