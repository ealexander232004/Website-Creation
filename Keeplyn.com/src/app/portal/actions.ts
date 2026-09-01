"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";
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

export async function approveWebsite(formData: FormData) {
  const requestId = requestIdSchema.parse(formData.get("requestId"));
  const supabase = await getAuthenticatedClient();
  const { error } = await supabase.rpc("approve_website_request", { p_request_id: requestId });
  if (error) throw new Error(error.message);
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
  const { error } = await supabase.from("website_request_updates").insert({
    request_id: input.requestId,
    title: input.title,
    description: input.description,
  });
  if (error) throw new Error(error.message);
  revalidatePath(`/portal/requests/${input.requestId}`);
}
