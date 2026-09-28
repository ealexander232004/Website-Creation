"use server";

import { z } from "zod";
import { sendContactInquiry } from "@/lib/email";

const inquirySchema = z.object({
  name: z.string().trim().min(2, "Add your name.").max(100),
  email: z.string().trim().email("Use a valid email address.").max(254),
  message: z.string().trim().min(10, "Tell us a little more.").max(2000),
});

export type InquiryState = { status: "idle" | "sent" | "error"; message?: string };

export async function submitInquiry(_previous: InquiryState, formData: FormData): Promise<InquiryState> {
  // Hidden field: people never fill it in, form bots usually do.
  if (String(formData.get("company_website") ?? "")) return { status: "sent" };

  const parsed = inquirySchema.safeParse({
    name: formData.get("name"),
    email: formData.get("email"),
    message: formData.get("message"),
  });
  if (!parsed.success) return { status: "error", message: parsed.error.issues[0]?.message ?? "Check the form and try again." };

  try {
    await sendContactInquiry(parsed.data);
    return { status: "sent" };
  } catch (error) {
    console.error("Contact inquiry failed", error);
    return { status: "error", message: "We couldn’t send that right now. Email support@keeplyn.com instead." };
  }
}
