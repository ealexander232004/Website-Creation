import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { AuthShell } from "@/components/auth-shell";
import { createClient } from "@/lib/supabase/server";
import { ResetPasswordForm } from "./reset-password-form";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Choose a new password" };

export default async function ResetPasswordPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  // Reached only through a verified recovery link, which signs the user in.
  if (!user) redirect("/auth/forgot-password?link=expired");

  return (
    <AuthShell
      kicker="Account recovery"
      title="Choose a new password."
      description={`Set a new password for ${user.email ?? "your account"}. You’ll stay signed in afterwards.`}
    >
      <ResetPasswordForm />
    </AuthShell>
  );
}
