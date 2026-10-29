export type OpsItemKind = "demo" | "revision" | "email_reply";
export type OpsItemStatus = "working" | "pending" | "approved" | "sent" | "rejected" | "failed" | "superseded";

export type OpsItem = {
  id: number;
  kind: OpsItemKind;
  status: OpsItemStatus;
  request_id: number | null;
  ticket_id: number | null;
  title: string;
  summary: string | null;
  demo_url: string | null;
  email_to: string | null;
  email_subject: string | null;
  inbound_body: string | null;
  draft_body: string | null;
  final_body: string | null;
  reviewer_note: string | null;
  source: Record<string, unknown>;
  result: string | null;
  created_at: string;
  updated_at: string;
  decided_at: string | null;
};

export const opsKindLabels: Record<OpsItemKind, string> = {
  demo: "New demo",
  revision: "Revision",
  email_reply: "Reply draft",
};

export const opsStatusLabels: Record<OpsItemStatus, string> = {
  working: "Being prepared",
  pending: "Waiting for you",
  approved: "Approved — sending",
  sent: "Sent",
  rejected: "Rejected",
  failed: "Failed",
  superseded: "Replaced",
};
