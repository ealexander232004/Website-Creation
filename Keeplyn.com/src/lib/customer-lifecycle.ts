export const requestStatuses = ["submitted", "in_review", "in_progress", "demo_ready", "changes_requested", "approved", "domain_pending", "payment_pending", "paid", "launching", "live", "cancelled"] as const;
export type RequestStatus = (typeof requestStatuses)[number];

export const statusLabels: Record<RequestStatus, string> = {
  submitted: "Request received", in_review: "In review", in_progress: "Website in progress", demo_ready: "Demo ready", changes_requested: "Updates requested", approved: "Approved", domain_pending: "Domain needed", payment_pending: "Ready for payment", paid: "Payment received", launching: "Launching", live: "Website live", cancelled: "Cancelled",
};

export const editableRequestStatuses: RequestStatus[] = ["submitted", "in_review", "in_progress", "demo_ready", "changes_requested"];

export type RequestOffering = { id: number; title: string; description: string; price: number | string; position: number };
export type RequestAsset = { id: number; storage_path: string; original_filename: string; mime_type: string; size_bytes: number; signedUrl?: string | null };
export type UpdateTicket = { id: number; request_id: number; title: string; description: string; status: "new" | "in_progress" | "completed"; admin_response: string | null; created_at: string; completed_at: string | null };
export type WebsiteRequest = {
  id: number; user_id: string; customer_name: string | null; customer_email: string | null; plan_id: "starter" | "pro"; photo_brief: string | null; theme_description: string | null; additional_notes: string | null; status: RequestStatus; demo_url: string | null; demo_ready_at: string | null; approved_at: string | null; domain_name: string | null; domain_submitted_at: string | null; hosting_selected: boolean; hosting_status: "not_selected" | "pending" | "active" | "past_due" | "cancelled"; payment_status: "not_ready" | "ready" | "pending" | "paid" | "failed" | "refunded"; stripe_checkout_session_id: string | null; stripe_customer_id: string | null; stripe_subscription_id: string | null; paid_at: string | null; live_url: string | null; live_at: string | null; created_at: string; updated_at: string; website_request_offerings?: RequestOffering[]; website_request_assets?: RequestAsset[]; website_request_updates?: UpdateTicket[];
};

export function formatRequestNumber(id: number) { return `#${String(id).padStart(4, "0")}`; }
export function formatDate(value: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}
