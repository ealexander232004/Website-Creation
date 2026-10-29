import "server-only";

import { Resend } from "resend";
import { formatRequestNumber } from "@/lib/customer-lifecycle";

type NotificationKind = "request_received" | "demo_ready" | "update_complete" | "payment_received" | "website_live";
type NotificationInput = {
  kind: NotificationKind;
  to: string;
  customerName?: string | null;
  requestId: number;
  detailUrl: string;
  idempotencyKey: string;
  demoUrl?: string | null;
  liveUrl?: string | null;
  message?: string | null;
};

const copy: Record<NotificationKind, { subject: string; heading: string; preview: string; body: string }> = {
  request_received: { subject: "We received your website request", heading: "Your request is in.", preview: "Keeplyn has received your website brief.", body: "We’re reviewing your brief now. Your custom demo will be ready within two business days, and you won’t pay until you approve it." },
  demo_ready: { subject: "Your Keeplyn website demo is ready", heading: "Your demo is ready.", preview: "Open your customer portal to review your new website.", body: "Review the demo in a new tab, then approve it or send us an update ticket from your request page." },
  update_complete: { subject: "Your requested website update is complete", heading: "Your update is complete.", preview: "Your latest Keeplyn website revision is ready to review.", body: "We finished the requested changes. Open your request to review the updated demo and approve it when everything feels right." },
  payment_received: { subject: "Payment received — your website is launching", heading: "We’re taking it live.", preview: "Keeplyn received your payment and is preparing your launch.", body: "Your payment is confirmed. We’re connecting your domain and completing the production launch now." },
  website_live: { subject: "Your Keeplyn website is live", heading: "You’re live.", preview: "Your new website is now live on your domain.", body: "Your website is live and ready to share. You can always return to your portal to see the request and submit future updates." },
};

function escapeHtml(value: string) {
  return value.replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character] ?? character);
}

export async function sendCustomerNotification(input: NotificationInput) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) throw new Error("RESEND_API_KEY is not configured.");
  const domain = process.env.RESEND_EMAIL_DOMAIN || "keeplyn.com";
  const content = copy[input.kind];
  const displayName = input.customerName?.trim() ? ` ${escapeHtml(input.customerName.trim())}` : "";
  const requestNumber = formatRequestNumber(input.requestId);
  const primaryUrl = input.kind === "website_live" && input.liveUrl ? input.liveUrl : input.detailUrl;
  const primaryLabel = input.kind === "website_live" ? "Visit your website" : "Open your request";
  const optionalMessage = input.message?.trim() ? `<div style="margin:24px 0;padding:18px;border-left:3px solid #c9ff3b;background:#f4f5f0;color:#252525;line-height:1.6">${escapeHtml(input.message.trim())}</div>` : "";
  const demoLink = input.demoUrl && input.kind !== "website_live" ? `<p style="margin:18px 0 0"><a href="${escapeHtml(input.demoUrl)}" style="color:#9ea7ff;text-decoration:underline">View the demo directly</a></p>` : "";
  const html = `<!doctype html><html><body style="margin:0;background:#efefe9;color:#111;font-family:Arial,Helvetica,sans-serif"><div style="display:none;max-height:0;overflow:hidden">${escapeHtml(content.preview)}</div><table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#efefe9"><tr><td align="center" style="padding:32px 16px"><table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px;background:#080808;color:#fff"><tr><td style="padding:32px 36px;border-bottom:1px solid #2a2a2a"><div style="font-size:22px;font-weight:800;letter-spacing:-1px">KEEP<span style="color:#c9ff3b">LYN</span></div></td></tr><tr><td style="padding:46px 36px"><p style="margin:0 0 18px;color:#c9ff3b;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase">Request ${requestNumber}</p><h1 style="margin:0;font-size:44px;line-height:1;letter-spacing:-2.5px">${escapeHtml(content.heading)}</h1><p style="margin:26px 0 0;color:#b8b8b8;font-size:16px;line-height:1.7">Hi${displayName}, ${escapeHtml(content.body)}</p>${optionalMessage}${demoLink}<p style="margin:32px 0 0"><a href="${escapeHtml(primaryUrl)}" style="display:inline-block;background:#c9ff3b;color:#050505;padding:14px 20px;font-size:13px;font-weight:800;text-decoration:none">${primaryLabel}</a></p></td></tr><tr><td style="padding:24px 36px;border-top:1px solid #2a2a2a;color:#777;font-size:12px;line-height:1.6">Keeplyn · The springboard for your small business<br><a href="mailto:support@keeplyn.com" style="color:#aaa">support@keeplyn.com</a></td></tr></table></td></tr></table></body></html>`;
  const text = `${content.heading}\n\nHi${input.customerName?.trim() ? ` ${input.customerName.trim()}` : ""}, ${content.body}\n\n${input.message?.trim() ? `${input.message.trim()}\n\n` : ""}${primaryLabel}: ${primaryUrl}\n\nRequest ${requestNumber}\nKeeplyn · support@keeplyn.com`;
  const resend = new Resend(apiKey);
  const { data, error } = await resend.emails.send({ from: `Keeplyn <updates@${domain}>`, replyTo: "support@keeplyn.com", to: input.to, subject: content.subject, html, text }, { headers: { "Idempotency-Key": input.idempotencyKey } });
  if (error) throw new Error(error.message);
  return data?.id ?? null;
}

export const KEEPLYN_SUPPORT_EMAIL = "support@keeplyn.com";

function sender() {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) throw new Error("RESEND_API_KEY is not configured.");
  return { resend: new Resend(apiKey), domain: process.env.RESEND_EMAIL_DOMAIN || "keeplyn.com" };
}

function plainEmail(lines: string[]) {
  const body = lines.map((line) => (line ? `<p style="margin:0 0 12px">${escapeHtml(line)}</p>` : "")).join("");
  return `<!doctype html><html><body style="margin:0;padding:28px;background:#f4f5f0;color:#151515;font:15px/1.6 Arial,Helvetica,sans-serif">${body}</body></html>`;
}

/** Tells Keeplyn that demos or reply drafts are waiting in /admin/approvals. */
export async function sendAdminApprovalsAlert(input: { items: { kind: string; title: string }[]; approvalsUrl: string; idempotencyKey: string }) {
  const { resend, domain } = sender();
  const count = input.items.length;
  const lines = [
    `${count} item${count === 1 ? " is" : "s are"} waiting for your approval:`,
    ...input.items.slice(0, 10).map((item) => `• ${item.kind}: ${item.title}`),
    `Review: ${input.approvalsUrl}`,
  ];
  const { error } = await resend.emails.send(
    { from: `Keeplyn <updates@${domain}>`, to: KEEPLYN_SUPPORT_EMAIL, subject: `${count} waiting for approval`, html: plainEmail(lines), text: lines.join("\n\n") },
    { headers: { "Idempotency-Key": input.idempotencyKey } },
  );
  if (error) throw new Error(error.message);
}

type AdminCustomer = { customerName?: string | null; customerEmail: string };

function describeCustomer({ customerName, customerEmail }: AdminCustomer) {
  return customerName?.trim() ? `${customerName.trim()} <${customerEmail}>` : customerEmail;
}

/** Plain internal alert to Keeplyn; replying goes straight to the customer. */
async function sendAdminAlert(input: AdminCustomer & { subject: string; lines: string[]; idempotencyKey: string }) {
  const { resend, domain } = sender();
  const { error } = await resend.emails.send(
    {
      from: `Keeplyn <updates@${domain}>`,
      to: KEEPLYN_SUPPORT_EMAIL,
      replyTo: input.customerEmail,
      subject: input.subject,
      html: plainEmail(input.lines),
      text: input.lines.join("\n\n"),
    },
    { headers: { "Idempotency-Key": input.idempotencyKey } },
  );
  if (error) throw new Error(error.message);
}

/** Tells Keeplyn a new website request is waiting in /admin. */
export async function sendAdminNewRequestAlert(input: AdminCustomer & { requestId: number; planId: string; businessName?: string | null; adminUrl: string }) {
  const requestNumber = formatRequestNumber(input.requestId);
  await sendAdminAlert({
    ...input,
    subject: `New website request ${requestNumber}${input.businessName ? `: ${input.businessName}` : ""} (${input.planId})`,
    lines: [
      `New ${input.planId} website request ${requestNumber}.`,
      ...(input.businessName ? [`Business: ${input.businessName}`] : []),
      `Customer: ${describeCustomer(input)}`,
      `Review it: ${input.adminUrl}`,
      "The customer was promised a demo within two business days.",
    ],
    idempotencyKey: `admin-new-request-${input.requestId}`,
  });
}

/** Tells Keeplyn a customer opened an update ticket (a demo revision or a post-launch change). */
export async function sendAdminTicketAlert(input: AdminCustomer & { requestId: number; ticketId: number; title: string; description: string; adminUrl: string }) {
  const requestNumber = formatRequestNumber(input.requestId);
  await sendAdminAlert({
    ...input,
    subject: `Update ticket on ${requestNumber}: ${input.title}`,
    lines: [
      `${describeCustomer(input)} opened an update ticket on request ${requestNumber}.`,
      input.title,
      ...input.description.split(/\n+/),
      `Respond in the admin: ${input.adminUrl}`,
      "Updates are promised in under two business days.",
    ],
    idempotencyKey: `admin-ticket-${input.ticketId}`,
  });
}

/** Tells Keeplyn a customer approved their demo and moved on to domain setup. */
export async function sendAdminApprovalAlert(input: AdminCustomer & { requestId: number; adminUrl: string }) {
  const requestNumber = formatRequestNumber(input.requestId);
  await sendAdminAlert({
    ...input,
    subject: `Request ${requestNumber} approved`,
    lines: [
      `${describeCustomer(input)} approved the demo for request ${requestNumber}.`,
      "They're now buying and connecting their domain, then paying through Stripe.",
      `Request: ${input.adminUrl}`,
    ],
    idempotencyKey: `admin-approved-${input.requestId}`,
  });
}

/** Tells Keeplyn a request is paid and ready to launch. */
export async function sendAdminPaymentAlert(input: AdminCustomer & { requestId: number; amount: string | null; domainName?: string | null; hosting: boolean; adminUrl: string }) {
  const requestNumber = formatRequestNumber(input.requestId);
  await sendAdminAlert({
    ...input,
    subject: `Payment received for ${requestNumber}${input.amount ? ` (${input.amount})` : ""}`,
    lines: [
      `${describeCustomer(input)} paid${input.amount ? ` ${input.amount}` : ""} for request ${requestNumber}.`,
      `Domain: ${input.domainName || "not recorded"}`,
      `Care plan: ${input.hosting ? "yes" : "no"}`,
      `Connect the domain, then mark the site live: ${input.adminUrl}`,
    ],
    idempotencyKey: `admin-payment-${input.requestId}`,
  });
}

/** Delivers a /contact inquiry to Keeplyn; replying goes straight to the visitor. */
export async function sendContactInquiry(input: { name: string; email: string; message: string }) {
  const { resend, domain } = sender();
  const lines = [`From: ${input.name} <${input.email}>`, "", ...input.message.split(/\n+/)];
  const { error } = await resend.emails.send({
    from: `Keeplyn website <updates@${domain}>`,
    to: KEEPLYN_SUPPORT_EMAIL,
    replyTo: input.email,
    subject: `Website inquiry from ${input.name}`,
    html: plainEmail(lines),
    text: lines.join("\n"),
  });
  if (error) throw new Error(error.message);
}
