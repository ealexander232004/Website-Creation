"use client";

import { ArrowUpRight, CheckCircle2, LoaderCircle } from "lucide-react";
import { useActionState } from "react";
import { submitInquiry, type InquiryState } from "@/app/contact/actions";

const fieldClass =
  "mt-2 w-full border border-white/14 bg-white/[0.045] px-4 py-3.5 text-[15px] text-white outline-none transition placeholder:text-white/24 focus:border-[#c9ff3b]/70 focus:bg-white/[0.07]";

export function ContactInquiryForm() {
  const [state, formAction, pending] = useActionState<InquiryState, FormData>(submitInquiry, { status: "idle" });

  if (state.status === "sent")
    return (
      <div className="border border-[#c9ff3b]/30 bg-[#c9ff3b]/[0.05] p-6 sm:p-8" role="status">
        <CheckCircle2 className="size-8 text-[#c9ff3b]" strokeWidth={1.5} aria-hidden="true" />
        <p className="mt-5 text-2xl font-semibold tracking-[-0.04em]">Message sent.</p>
        <p className="mt-3 text-sm leading-6 text-white/52">Thanks for reaching out. We’ll reply to your email soon.</p>
      </div>
    );

  return (
    <form action={formAction} className="border border-white/14 bg-white/[0.035] p-6 sm:p-8">
      <div>
        <label htmlFor="inquiry-name" className="text-sm font-medium text-white/76">
          Name
        </label>
        <input id="inquiry-name" name="name" type="text" autoComplete="name" maxLength={100} required placeholder="Your name" className={fieldClass} />
      </div>

      <div className="mt-5">
        <label htmlFor="inquiry-email" className="text-sm font-medium text-white/76">
          Email
        </label>
        <input id="inquiry-email" name="email" type="email" autoComplete="email" maxLength={254} required placeholder="you@company.com" className={fieldClass} />
      </div>

      <div className="mt-5">
        <label htmlFor="inquiry-message" className="text-sm font-medium text-white/76">
          How can we help?
        </label>
        <textarea id="inquiry-message" name="message" rows={6} minLength={10} maxLength={2000} required placeholder="Tell us what you would like to know." className={`${fieldClass} resize-y`} />
      </div>

      {/* Honeypot: hidden from people and assistive tech. */}
      <div className="absolute -left-[9999px] size-px overflow-hidden" aria-hidden="true">
        <label>
          Company website
          <input name="company_website" type="text" tabIndex={-1} autoComplete="off" />
        </label>
      </div>

      <button type="submit" className="button-primary mt-6" disabled={pending}>
        {pending ? <LoaderCircle className="size-4 animate-spin" aria-hidden="true" /> : null}
        Submit inquiry
        {!pending ? <ArrowUpRight className="size-4" aria-hidden="true" /> : null}
      </button>

      {state.status === "error" ? (
        <p className="mt-4 text-sm leading-6 text-[#ffb4a8]" role="alert">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
