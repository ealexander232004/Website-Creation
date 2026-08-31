import type { Metadata } from "next";
import { WebsiteRequestFlow } from "@/components/website-request-flow";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Start your website",
  description:
    "Choose your Keeplyn plan and tell us what your new website needs.",
};

type StartPageProps = {
  searchParams: Promise<{
    plan?: string;
    verified?: string;
    auth_error?: string;
  }>;
};

export default async function StartPage({ searchParams }: StartPageProps) {
  const params = await searchParams;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <WebsiteRequestFlow
      initialPlan={params.plan === "starter" || params.plan === "pro" ? params.plan : null}
      verificationComplete={params.verified === "1"}
      authError={params.auth_error === "verification"}
      initialUser={
        user
          ? {
              id: user.id,
              email: user.email ?? "",
              name:
                typeof user.user_metadata.full_name === "string"
                  ? user.user_metadata.full_name
                  : "",
              emailConfirmed: Boolean(user.email_confirmed_at),
            }
          : null
      }
    />
  );
}
