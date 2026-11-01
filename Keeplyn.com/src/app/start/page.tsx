import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { WebsiteRequestFlow } from "@/components/website-request-flow";
import { safeNextPath } from "@/lib/safe-redirect";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Start your website",
  description:
    "Choose your Keeplyn plan and tell us what your new website needs.",
};

type StartPageProps = {
  searchParams: Promise<{
    mode?: string;
    plan?: string;
    link?: string;
    next?: string;
    confirmed?: string;
  }>;
};

export default async function StartPage({ searchParams }: StartPageProps) {
  const params = await searchParams;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const signingIn = params.mode === "signin";
  // Where to go after signing in: the page that sent them here, else the portal.
  const nextPath = signingIn ? safeNextPath(params.next, "/portal") : null;
  if (user && nextPath) redirect(nextPath);

  return (
    <WebsiteRequestFlow
      initialAccountMode={signingIn ? "signin" : "signup"}
      nextPath={nextPath}
      expiredLink={params.link === "expired"}
      confirmed={params.confirmed === "1"}
      initialPlan={params.plan === "starter" || params.plan === "pro" ? params.plan : null}
      initialUser={
        user
          ? {
              id: user.id,
              email: user.email ?? "",
              name:
                typeof user.user_metadata.full_name === "string"
                  ? user.user_metadata.full_name
                  : "",
            }
          : null
      }
    />
  );
}
