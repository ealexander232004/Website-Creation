import type { EmailOtpType } from "@supabase/supabase-js";
import { NextResponse, type NextRequest } from "next/server";
import { safeNextPath } from "@/lib/safe-redirect";
import { createClient } from "@/lib/supabase/server";

// Email links land here: sign-up confirmation and password recovery.
// Supports the token-hash templates and the default PKCE `code` links.
export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const tokenHash = searchParams.get("token_hash");
  const type = searchParams.get("type") as EmailOtpType | null;
  const code = searchParams.get("code");
  const next = safeNextPath(
    searchParams.get("next"),
    type === "recovery" ? "/auth/reset-password" : "/start",
  );

  const supabase = await createClient();
  let ok = false;
  if (tokenHash && type) {
    ok = !(await supabase.auth.verifyOtp({ type, token_hash: tokenHash })).error;
  } else if (code) {
    ok = !(await supabase.auth.exchangeCodeForSession(code)).error;
  }

  const destination = request.nextUrl.clone();
  destination.search = "";
  if (ok) {
    // `next` may carry a query (e.g. /start?confirmed=1).
    const target = new URL(next, destination.origin);
    destination.pathname = target.pathname;
    destination.search = target.search;
  } else if (type === "recovery" || next === "/auth/reset-password") {
    destination.pathname = "/auth/forgot-password";
    destination.searchParams.set("link", "expired");
  } else {
    destination.pathname = "/start";
    destination.searchParams.set("mode", "signin");
    destination.searchParams.set("link", "expired");
    if (next !== "/start") destination.searchParams.set("next", next);
  }
  return NextResponse.redirect(destination);
}
