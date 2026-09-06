"use client";

import { useState, type FormEvent } from "react";
import { ArrowUpRight, Check, RotateCcw } from "lucide-react";
import type { BusinessTemplate } from "./catalog";

export function TemplateForm({
  business: b,
  booking = false,
}: {
  business: BusinessTemplate;
  booking?: boolean;
}) {
  const [time, setTime] = useState("9:30 AM");
  const [receipt, setReceipt] = useState<{
    name: string;
    service: string;
    date: string;
  } | null>(null);
  const isAppointment = booking && b.id !== "sera";
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const date = form.elements.namedItem("date") as HTMLInputElement | null;
    if (date?.value && new Date(`${date.value}T23:59:59`) < new Date()) {
      date.setCustomValidity("Please choose today or a future date.");
      date.reportValidity();
      return;
    }
    const data = new FormData(form);
    setReceipt({
      name: String(data.get("name")).trim().split(" ")[0],
      service: String(data.get("service")),
      date: String(data.get("date") ?? ""),
    });
  }
  if (receipt)
    return (
      <div
        className="template-form-receipt"
        role="status"
        tabIndex={-1}
        ref={(node) => node?.focus()}
      >
        <span className="template-receipt-check">
          <Check size={30} aria-hidden="true" />
        </span>
        <span className="template-eyebrow">You have tried the demo</span>
        <h2>
          Looks good,
          <br />
          {receipt.name}.
        </h2>
        <p>
          {receipt.service}
          {receipt.date ? ` · ${receipt.date}` : ""}
          {isAppointment ? ` · ${time}` : ""}
        </p>
        <p className="template-form-note">
          This is a preview. Nothing was sent, and no booking or order was
          placed.
        </p>
        <button
          className="template-button"
          type="button"
          onClick={() => setReceipt(null)}
        >
          Try again <RotateCcw size={18} aria-hidden="true" />
        </button>
      </div>
    );
  return (
    <form className="template-form" onSubmit={submit}>
      <p className="template-form-note">
        Try the form. This concept demo does not send messages or make real
        bookings.
      </p>
      <div className="template-form-pair">
        <label>
          Your name
          <input
            name="name"
            autoComplete="name"
            placeholder="Alex Morgan"
            required
            maxLength={100}
          />
        </label>
        <label>
          Email address
          <input
            name="email"
            type="email"
            autoComplete="email"
            placeholder="alex@example.com"
            required
          />
        </label>
      </div>
      <label>
        {b.id === "sera" ? "What are you planning?" : "How can we help?"}
        <select name="service" defaultValue="" required>
          <option value="" disabled>
            Choose an option
          </option>
          {b.packages.map((p) => (
            <option key={p.name}>{p.name}</option>
          ))}
          <option>Something else</option>
        </select>
      </label>
      {booking && (
        <label>
          {b.id === "sera" ? "Preferred pickup date" : "Preferred date"}
          <input
            name="date"
            type="date"
            required
            onChange={(e) => e.currentTarget.setCustomValidity("")}
          />
        </label>
      )}
      {isAppointment && (
        <fieldset>
          <legend>
            Preferred time <span> / sample times</span>
          </legend>
          <div className="template-time-slots">
            {["9:30 AM", "11:00 AM", "2:30 PM"].map((slot) => (
              <button
                type="button"
                key={slot}
                aria-pressed={slot === time}
                onClick={() => setTime(slot)}
              >
                {slot}
              </button>
            ))}
          </div>
        </fieldset>
      )}
      <label>
        {b.id === "sera"
          ? "How many people? Any special requests?"
          : "Anything you would like us to know?"}
        <textarea
          name="message"
          rows={3}
          placeholder={
            b.id === "moss"
              ? "A little about your space…"
              : b.id === "sera"
                ? "A birthday brunch for twelve…"
                : "Questions, preferences, or access needs…"
          }
          required={!booking}
          maxLength={3000}
        />
      </label>
      <button type="submit" className="template-button">
        {booking ? "Preview request" : "Preview inquiry"}
        <ArrowUpRight size={19} aria-hidden="true" />
      </button>
    </form>
  );
}
