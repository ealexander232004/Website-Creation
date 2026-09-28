"use client";

import { ArrowRight, LoaderCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import { authFieldClass } from "@/components/auth-shell";
import { createClient } from "@/lib/supabase/client";

export function ResetPasswordForm() {
  const supabase = useMemo(() => createClient(), []);
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (password.length < 8) return setError("Use at least 8 characters.");
    if (password !== confirm) return setError("Those passwords don’t match.");
    setBusy(true);
    const { error: updateError } = await supabase.auth.updateUser({ password });
    setBusy(false);
    if (updateError) {
      setError(
        updateError.code === "same_password"
          ? "Choose a password you haven’t used for this account."
          : "We couldn’t update your password. Request a new reset link and try again.",
      );
      return;
    }
    router.replace("/portal");
    router.refresh();
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error ? (
        <p className="border border-[#ff8f7e]/30 bg-[#ff725e]/8 px-4 py-3 text-sm text-[#ffb4a8]" role="alert">{error}</p>
      ) : null}
      <label className="block text-xs font-semibold text-white/62">
        New password
        <input className={authFieldClass} type="password" autoComplete="new-password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" required />
      </label>
      <label className="block text-xs font-semibold text-white/62">
        Confirm new password
        <input className={authFieldClass} type="password" autoComplete="new-password" minLength={8} value={confirm} onChange={(event) => setConfirm(event.target.value)} required />
      </label>
      <button type="submit" className="button-primary" disabled={busy}>
        {busy ? <LoaderCircle className="size-4 animate-spin" aria-hidden="true" /> : null}
        Save new password
        {!busy ? <ArrowRight className="size-4" aria-hidden="true" /> : null}
      </button>
    </form>
  );
}
