import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

function safeDestination(value: string | null) {
  return value?.startsWith("/") && !value.startsWith("//") ? value : "/start";
}

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const destination = safeDestination(requestUrl.searchParams.get("next"));

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error) {
      const verifiedUrl = new URL(destination, requestUrl.origin);
      verifiedUrl.searchParams.set("verified", "1");
      return NextResponse.redirect(verifiedUrl);
    }
  }

  return NextResponse.redirect(
    new URL("/start?auth_error=verification", requestUrl.origin),
  );
}
