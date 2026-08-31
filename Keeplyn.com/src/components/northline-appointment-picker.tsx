"use client";

import { ArrowRight, CalendarDays, Clock3 } from "lucide-react";
import { useState } from "react";

const appointmentConfigs = {
  northline: {
    subject: "Northline demo appointment request",
    serviceLabel: "What brings you in?",
    services: ["New patient visit", "Preventive visit", "Restorative care", "Cosmetic consultation", "Urgent concern"],
    availability: [
      { date: "2026-09-08", day: "Tue", label: "Sep 8", times: ["9:30 AM", "11:00 AM", "2:15 PM"] },
      { date: "2026-09-09", day: "Wed", label: "Sep 9", times: ["8:15 AM", "10:45 AM", "3:30 PM"] },
      { date: "2026-09-10", day: "Thu", label: "Sep 10", times: ["9:00 AM", "1:00 PM", "4:00 PM"] },
      { date: "2026-09-15", day: "Tue", label: "Sep 15", times: ["8:30 AM", "12:30 PM", "3:45 PM"] },
    ],
    notePlaceholder: "Accessibility needs, symptoms, or a preferred provider.",
    selectionLabel: "Selected appointment",
    submitLabel: "Request appointment",
    inputClassName: "rounded-xl border border-[#173a5a]/16 bg-[#f3f7fb] placeholder:text-[#173a5a]/35 focus:border-[#ff725e]",
    iconClassName: "text-[#ff725e]",
    selectedDateClassName: "border-[#173a5a] bg-[#173a5a] text-white",
    dateClassName: "border-[#173a5a]/14 bg-[#f3f7fb] text-[#173a5a]/60 hover:border-[#ff725e] hover:text-[#173a5a]",
    selectedTimeClassName: "border-[#ff725e] bg-[#ff725e] text-white",
    timeClassName: "border-[#173a5a]/14 text-[#173a5a]/58 hover:border-[#ff725e] hover:text-[#173a5a]",
    summaryClassName: "rounded-2xl bg-[#dcebf6]",
    mutedClassName: "text-[#173a5a]/42",
    submitClassName: "rounded-full bg-[#ff725e] text-white",
  },
  moss: {
    subject: "Moss & Mortar demo consultation request",
    serviceLabel: "What would you like to grow?",
    services: ["Planting plan", "Garden design", "Full landscape", "Not sure yet"],
    availability: [
      { date: "2026-09-17", day: "Thu", label: "Sep 17", times: ["9:00 AM", "11:30 AM", "3:00 PM"] },
      { date: "2026-09-22", day: "Tue", label: "Sep 22", times: ["8:30 AM", "1:00 PM", "4:30 PM"] },
      { date: "2026-09-24", day: "Thu", label: "Sep 24", times: ["10:00 AM", "12:30 PM", "3:30 PM"] },
      { date: "2026-10-01", day: "Thu", label: "Oct 1", times: ["9:30 AM", "11:00 AM", "2:00 PM"] },
    ],
    notePlaceholder: "Location, property size, access needs, or anything else we should know.",
    selectionLabel: "Selected consultation",
    submitLabel: "Request consultation",
    inputClassName: "border border-[#203126]/22 bg-transparent placeholder:text-[#203126]/35 focus:border-[#203126]",
    iconClassName: "text-[#203126]",
    selectedDateClassName: "border-[#203126] bg-[#203126] text-[#edf1e9]",
    dateClassName: "border-[#203126]/18 bg-[#edf1e9] text-[#203126]/62 hover:border-[#203126] hover:text-[#203126]",
    selectedTimeClassName: "border-[#203126] bg-[#203126] text-[#edf1e9]",
    timeClassName: "border-[#203126]/20 text-[#203126]/62 hover:border-[#203126] hover:text-[#203126]",
    summaryClassName: "border border-[#203126]/16 bg-[#dfe5d6]",
    mutedClassName: "text-[#203126]/46",
    submitClassName: "bg-[#203126] text-[#edf1e9]",
  },
} as const;

type AppointmentKind = keyof typeof appointmentConfigs;

function DemoAppointmentPicker({ kind }: { kind: AppointmentKind }) {
  const config = appointmentConfigs[kind];
  const [selectedDayIndex, setSelectedDayIndex] = useState(0);
  const [selectedTime, setSelectedTime] = useState<string>(
    config.availability[0].times[0],
  );
  const selectedDay = config.availability[selectedDayIndex];

  const selectDay = (index: number) => {
    setSelectedDayIndex(index);
    setSelectedTime(config.availability[index].times[0]);
  };

  const inputClassName = `min-h-12 min-w-0 w-full px-4 py-3 text-sm outline-none ${config.inputClassName}`;

  return (
    <form
      action="mailto:hello@keeplyn.com"
      method="post"
      encType="text/plain"
      className="grid gap-7"
    >
      <input
        type="hidden"
        name="subject"
        value={config.subject}
      />
      <input type="hidden" name="appointment-date" value={selectedDay.date} />
      <input type="hidden" name="appointment-time" value={selectedTime} />

      <div className="grid grid-cols-[repeat(auto-fit,minmax(min(14rem,100%),1fr))] gap-5">
        <label className="grid min-w-0 gap-2 text-xs font-semibold">
          Name
          <input
            required
            autoComplete="name"
            name="name"
            className={inputClassName}
            placeholder="Your name"
          />
        </label>
        <label className="grid min-w-0 gap-2 text-xs font-semibold">
          Email
          <input
            required
            autoComplete="email"
            name="email"
            type="email"
            className={inputClassName}
            placeholder="you@example.com"
          />
        </label>
      </div>

      <label className="grid min-w-0 gap-2 text-xs font-semibold">
        {config.serviceLabel}
        <select
          required
          name="visit-type"
          className={inputClassName}
          defaultValue=""
        >
          <option value="" disabled>
            Choose one
          </option>
          {config.services.map((service) => <option key={service}>{service}</option>)}
        </select>
      </label>

      <fieldset>
        <legend className="flex items-center gap-2 text-xs font-semibold">
          <CalendarDays className={`size-4 ${config.iconClassName}`} aria-hidden="true" />
          Choose an available date
        </legend>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {config.availability.map((day, index) => {
            const isSelected = index === selectedDayIndex;

            return (
              <button
                key={day.date}
                type="button"
                aria-pressed={isSelected}
                onClick={() => selectDay(index)}
                className={`rounded-xl border px-3 py-3 text-left transition-colors ${
                  isSelected
                    ? config.selectedDateClassName
                    : config.dateClassName
                }`}
              >
                <span className="block text-[9px] font-semibold uppercase tracking-[0.14em] opacity-55">
                  {day.day}
                </span>
                <time dateTime={day.date} className="mt-1 block text-sm font-semibold">
                  {day.label}
                </time>
              </button>
            );
          })}
        </div>
      </fieldset>

      <fieldset>
        <legend className="flex items-center gap-2 text-xs font-semibold">
          <Clock3 className={`size-4 ${config.iconClassName}`} aria-hidden="true" />
          Choose a time
        </legend>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
          {selectedDay.times.map((time) => {
            const isSelected = time === selectedTime;

            return (
              <button
                key={time}
                type="button"
                aria-pressed={isSelected}
                onClick={() => setSelectedTime(time)}
                className={`rounded-full border px-4 py-2.5 text-xs font-semibold transition-colors ${
                  isSelected
                    ? config.selectedTimeClassName
                    : config.timeClassName
                }`}
              >
                {time}
              </button>
            );
          })}
        </div>
      </fieldset>

      <label className="grid min-w-0 gap-2 text-xs font-semibold">
        <span className="flex items-center gap-2">
          Anything we should know?
          <span className={`font-normal ${config.mutedClassName}`}>Optional</span>
        </span>
        <textarea
          name="notes"
          rows={3}
          className={`${inputClassName} resize-y`}
          placeholder={config.notePlaceholder}
        />
      </label>

      <div className={`flex flex-col gap-2 px-5 py-4 sm:flex-row sm:items-center sm:justify-between ${config.summaryClassName}`}>
        <div>
          <p className={`text-[9px] font-semibold uppercase tracking-[0.14em] ${config.mutedClassName}`}>
            {config.selectionLabel}
          </p>
          <p className="mt-1 text-sm font-semibold">
            {selectedDay.day}, {selectedDay.label} at {selectedTime}
          </p>
        </div>
        <p className={`text-[10px] ${config.mutedClassName}`}>Demo availability</p>
      </div>

      <button
        type="submit"
        className={`flex items-center justify-between px-5 py-4 text-sm font-semibold ${config.submitClassName}`}
      >
        {config.submitLabel}
        <ArrowRight className="size-4" aria-hidden="true" />
      </button>
    </form>
  );
}

export function NorthlineAppointmentPicker() {
  return <DemoAppointmentPicker kind="northline" />;
}

export function MossAppointmentPicker() {
  return <DemoAppointmentPicker kind="moss" />;
}
