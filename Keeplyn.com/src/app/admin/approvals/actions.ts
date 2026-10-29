"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";
import { sendCustomerNotification } from "@/lib/email";
import type { OpsItem } from "@/lib/ops";
import { getEmailOrigin } from "@/lib/site-url";
import { createClient } from "@/lib/supabase/server";

const idSchema = z.coerce.number().int().positive();
const bodySchema = z.string().trim().min(1, "Write the message before approving.").max(10000);
const noteSchema = z.string().trim().max(4000);

async function requireAdmin() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/start?mode=signin");
  const { data } = await supabase.rpc("is_keeplyn_admin");
  if (!data) redirect("/portal");
  return supabase;
}

type Supabase = Awaited<ReturnType<typeof requireAdmin>>;

async function decide(supabase: Supabase, itemId: number, decision: "approve" | "reject", finalBody?: string | null, note?: string | null) {
  const { data, error } = await supabase.rpc("admin_decide_ops_item", { p_item_id: itemId, p_decision: decision, p_final_body: finalBody ?? null, p_note: note ?? null });
  if (error || !data) throw new Error(error?.message || "Approval item not found.");
  return data as OpsItem;
}

async function finish(supabase: Supabase, itemId: number, status: "sent" | "failed", result?: string) {
  const { error } = await supabase.rpc("admin_finish_ops_item", { p_item_id: itemId, p_status: status, p_result: result ?? null });
  if (error) throw new Error(error.message);
}

async function customerFor(supabase: Supabase, requestId: number) {
  const { data, error } = await supabase.from("website_requests").select("id, customer_name, customer_email, demo_url").eq("id", requestId).single();
  if (error || !data?.customer_email) throw new Error("Customer email is unavailable.");
  return data;
}

function refresh(requestId?: number | null) {
  revalidatePath("/admin/approvals");
  revalidatePath("/admin");
  if (requestId) {
    revalidatePath(`/admin/requests/${requestId}`);
    revalidatePath(`/portal/requests/${requestId}`);
  }
}

/** Publishes a finished demo to the customer: sets it on the request and sends the demo-ready email. */
export async function approveDemo(formData: FormData) {
  const itemId = idSchema.parse(formData.get("itemId"));
  const supabase = await requireAdmin();
  const item = await decide(supabase, itemId, "approve");
  try {
    if (item.kind !== "demo" || !item.request_id || !item.demo_url) throw new Error("This item has no demo to publish.");
    const { error } = await supabase.rpc("admin_set_demo", { p_request_id: item.request_id, p_demo_url: item.demo_url });
    if (error) throw new Error(error.message);
    const request = await customerFor(supabase, item.request_id);
    const origin = await getEmailOrigin();
    await sendCustomerNotification({ kind: "demo_ready", to: request.customer_email, customerName: request.customer_name, requestId: item.request_id, detailUrl: `${origin}/portal/requests/${item.request_id}`, demoUrl: item.demo_url, idempotencyKey: `ops-demo-${item.id}` });
    await finish(supabase, item.id, "sent");
  } catch (error) {
    await finish(supabase, item.id, "failed", error instanceof Error ? error.message : String(error));
    throw error;
  } finally {
    refresh(item.request_id);
  }
}

/**
 * Completes the customer's update ticket with the approved message and emails them.
 * The worker promotes the reviewed preview to the customer's demo address once this is approved.
 */
export async function approveRevision(formData: FormData) {
  const itemId = idSchema.parse(formData.get("itemId"));
  const message = bodySchema.parse(formData.get("message"));
  const supabase = await requireAdmin();
  const item = await decide(supabase, itemId, "approve", message);
  try {
    if (item.kind !== "revision" || !item.request_id) throw new Error("This item is not a revision.");
    if (item.ticket_id) {
      const { error } = await supabase.rpc("admin_set_update_ticket", { p_ticket_id: item.ticket_id, p_status: "completed", p_admin_response: message });
      if (error) throw new Error(error.message);
    }
    const request = await customerFor(supabase, item.request_id);
    const origin = await getEmailOrigin();
    await sendCustomerNotification({ kind: "update_complete", to: request.customer_email, customerName: request.customer_name, requestId: item.request_id, detailUrl: `${origin}/portal/requests/${item.request_id}`, demoUrl: request.demo_url, message, idempotencyKey: `ops-revision-${item.id}` });
    await finish(supabase, item.id, "sent");
  } catch (error) {
    await finish(supabase, item.id, "failed", error instanceof Error ? error.message : String(error));
    throw error;
  } finally {
    refresh(item.request_id);
  }
}

/** Approves a reply draft; the ops worker sends it from the original mailbox within a minute. */
export async function approveEmail(formData: FormData) {
  const itemId = idSchema.parse(formData.get("itemId"));
  const body = bodySchema.parse(formData.get("body"));
  const supabase = await requireAdmin();
  await decide(supabase, itemId, "approve", body);
  refresh();
}

/** Rejects an item. For demos and revisions the note goes back to the builder as a change request. */
export async function rejectItem(formData: FormData) {
  const itemId = idSchema.parse(formData.get("itemId"));
  const note = noteSchema.parse(formData.get("note") ?? "");
  const supabase = await requireAdmin();
  const item = await decide(supabase, itemId, "reject", null, note || null);
  refresh(item.request_id);
}
