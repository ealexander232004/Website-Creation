"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";
import { sendAdminApprovalAlert, sendAdminTicketAlert } from "@/lib/email";
import { getEmailOrigin } from "@/lib/site-url";
import { createClient } from "@/lib/supabase/server";

const requestIdSchema = z.coerce.number().int().positive();
const ticketSchema = z.object({
  requestId: requestIdSchema,
  title: z.string().trim().min(2).max(120),
  description: z.string().trim().min(2).max(5000),
});

async function getAuthenticatedClient() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/start?mode=signin");
  return supabase;
}

async function getCustomer(supabase: Awaited<ReturnType<typeof createClient>>, requestId: number) {
  const { data } = await supabase.from("website_requests").select("customer_name, customer_email").eq("id", requestId).single();
  return data?.customer_email ? { customerName: data.customer_name, customerEmail: data.customer_email } : null;
}

export async function approveWebsite(formData: FormData) {
  const requestId = requestIdSchema.parse(formData.get("requestId"));
  const supabase = await getAuthenticatedClient();
  const { error } = await supabase.rpc("approve_website_request", { p_request_id: requestId });
  if (error) throw new Error(error.message);
  try {
    const customer = await getCustomer(supabase, requestId);
    if (customer) await sendAdminApprovalAlert({ ...customer, requestId, adminUrl: `${await getEmailOrigin()}/admin/requests/${requestId}` });
  } catch (alertError) {
    // The approval is saved; a failed internal alert must not block domain setup.
    console.error("Approval admin alert failed", { requestId, alertError });
  }
  revalidatePath(`/portal/requests/${requestId}`);
  redirect(`/portal/requests/${requestId}/domain`);
}

export async function createUpdateTicket(formData: FormData) {
  const input = ticketSchema.parse({
    requestId: formData.get("requestId"),
    title: formData.get("title"),
    description: formData.get("description"),
  });
  const supabase = await getAuthenticatedClient();
  const { data: ticket, error } = await supabase.from("website_request_updates").insert({
    request_id: input.requestId,
    title: input.title,
    description: input.description,
  }).select("id").single();
  if (error) throw new Error(error.message);
  try {
    const customer = await getCustomer(supabase, input.requestId);
    if (customer) await sendAdminTicketAlert({ ...customer, requestId: input.requestId, ticketId: ticket.id, title: input.title, description: input.description, adminUrl: `${await getEmailOrigin()}/admin/requests/${input.requestId}` });
  } catch (alertError) {
    console.error("Update ticket admin alert failed", { requestId: input.requestId, alertError });
  }
  revalidatePath(`/portal/requests/${input.requestId}`);
}
