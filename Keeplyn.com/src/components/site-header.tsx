import { createClient } from "@/lib/supabase/server";
import { SiteHeaderClient } from "./site-header-client";

export async function SiteHeader() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return <SiteHeaderClient authenticated={Boolean(user)} />;
}
