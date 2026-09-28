import type { Metadata } from "next";
import { AuthShell } from "@/components/auth-shell";
import { ForgotPasswordForm } from "./forgot-password-form";

export const metadata: Metadata = {
  title: "Reset your password",
  description: "Get a secure link to choose a new Keeplyn password.",
};

export default async function ForgotPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ link?: string }>;
}) {
  const { link } = await searchParams;
  return (
    <AuthShell
      kicker="Account recovery"
      title="Forgot your password?"
      description="Enter the email you use with Keeplyn. We’ll send a secure link to choose a new password."
    >
      <ForgotPasswordForm expired={link === "expired"} />
    </AuthShell>
  );
}
