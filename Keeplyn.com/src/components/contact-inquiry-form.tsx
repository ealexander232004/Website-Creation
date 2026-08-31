"use client";

import { ArrowUpRight } from "lucide-react";
import { FormEvent, useState } from "react";

const fieldClass =
  "mt-2 w-full border border-white/14 bg-white/[0.045] px-4 py-3.5 text-[15px] text-white outline-none transition placeholder:text-white/24 focus:border-[#c9ff3b]/70 focus:bg-white/[0.07]";

export function ContactInquiryForm() {
  const [status, setStatus] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus(
      "This preview is not sending inquiries yet. Your message remains in the form while we connect email delivery.",
    );
  }

  return (
    <form
      className="border border-white/14 bg-white/[0.035] p-6 sm:p-8"
      onSubmit={handleSubmit}
    >
      <div>
        <label htmlFor="inquiry-name" className="text-sm font-medium text-white/76">
          Name
        </label>
        <input
          id="inquiry-name"
          name="name"
          type="text"
          autoComplete="name"
          maxLength={100}
          required
          placeholder="Your name"
          className={fieldClass}
        />
      </div>

      <div className="mt-5">
        <label htmlFor="inquiry-email" className="text-sm font-medium text-white/76">
          Email
        </label>
        <input
          id="inquiry-email"
          name="email"
          type="email"
          autoComplete="email"
          maxLength={254}
          required
          placeholder="you@company.com"
          className={fieldClass}
        />
      </div>

      <div className="mt-5">
        <label htmlFor="inquiry-message" className="text-sm font-medium text-white/76">
          How can we help?
        </label>
        <textarea
          id="inquiry-message"
          name="message"
          rows={6}
          maxLength={2000}
          required
          placeholder="Tell us what you would like to know."
          className={`${fieldClass} resize-y`}
        />
      </div>

      <button type="submit" className="button-primary mt-6">
        Submit inquiry
        <ArrowUpRight className="size-4" aria-hidden="true" />
      </button>

      <p className="mt-4 text-xs leading-5 text-white/38">
        Email delivery will be connected before launch.
      </p>
      <p className="mt-3 text-sm leading-6 text-[#c9ff3b]" aria-live="polite">
        {status}
      </p>
    </form>
  );
}
