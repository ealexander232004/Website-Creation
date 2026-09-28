"use client";

import { ArrowRight, LoaderCircle, MailCheck } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { authFieldClass } from "@/components/auth-shell";
import { createClient } from "@/lib/supabase/client";

export function ForgotPasswordForm({ expired }: { expired: boolean }) {
  const supabase = useMemo(() => createClient(), []);
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(
    expired ? "That reset link has expired or was already used. Request a new one below." : null,
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    const { error: resetError } = await supabase.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: `${window.location.origin}/auth/confirm?next=/auth/reset-password`,
    });
    setBusy(false);
    // Don't reveal whether an account exists; only surface rate limits and outages.
    if (resetError && resetError.status !== 400 && resetError.status !== 404) {
      setError("We couldn’t send the link right now. Please try again in a minute.");
      return;
    }
    setSent(true);
  }

  if (sent)
    return (
      <div className="border border-[#c9ff3b]/30 bg-[#c9ff3b]/[0.05] p-6" role="status">
        <MailCheck className="size-7 text-[#c9ff3b]" aria-hidden="true" />
        <p className="mt-4 text-lg font-semibold tracking-[-0.03em]">Check your inbox.</p>
        <p className="mt-2 text-sm leading-6 text-white/52">
          If an account exists for <strong className="text-white/80">{email.trim()}</strong>, a reset link is on its way. It works once and expires after an hour.
        </p>
      </div>
    );

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error ? (
        <p className="border border-[#ff8f7e]/30 bg-[#ff725e]/8 px-4 py-3 text-sm text-[#ffb4a8]" role="alert">{error}</p>
      ) : null}
      <label className="block text-xs font-semibold text-white/62">
        Email address
        <input
          className={authFieldClass}
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@business.com"
          required
        />
      </label>
      <button type="submit" className="button-primary" disabled={busy}>
        {busy ? <LoaderCircle className="size-4 animate-spin" aria-hidden="true" /> : null}
        Send reset link
        {!busy ? <ArrowRight className="size-4" aria-hidden="true" /> : null}
      </button>
    </form>
  );
}
