"use client";

import { ArrowRight, CalendarDays, Clock3 } from "lucide-react";
import { useState } from "react";

const appointmentAvailability = [
  {
    date: "2026-09-08",
    day: "Tue",
    label: "Sep 8",
    times: ["9:30 AM", "11:00 AM", "2:15 PM"],
  },
  {
    date: "2026-09-09",
    day: "Wed",
    label: "Sep 9",
    times: ["8:15 AM", "10:45 AM", "3:30 PM"],
  },
  {
    date: "2026-09-10",
    day: "Thu",
    label: "Sep 10",
    times: ["9:00 AM", "1:00 PM", "4:00 PM"],
  },
  {
    date: "2026-09-15",
    day: "Tue",
    label: "Sep 15",
    times: ["8:30 AM", "12:30 PM", "3:45 PM"],
  },
] as const;

const inputClassName =
  "min-h-12 w-full rounded-xl border border-[#173a5a]/16 bg-[#f3f7fb] px-4 py-3 text-sm outline-none placeholder:text-[#173a5a]/35 focus:border-[#ff725e]";

export function NorthlineAppointmentPicker() {
  const [selectedDayIndex, setSelectedDayIndex] = useState(0);
  const [selectedTime, setSelectedTime] = useState<string>(
    appointmentAvailability[0].times[0],
  );
  const selectedDay = appointmentAvailability[selectedDayIndex];

  const selectDay = (index: number) => {
    setSelectedDayIndex(index);
    setSelectedTime(appointmentAvailability[index].times[0]);
  };

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
        value="Northline demo appointment request"
      />
      <input type="hidden" name="appointment-date" value={selectedDay.date} />
      <input type="hidden" name="appointment-time" value={selectedTime} />

      <div className="grid gap-5 sm:grid-cols-2">
        <label className="grid gap-2 text-xs font-semibold">
          Name
          <input
            required
            autoComplete="name"
            name="name"
            className={inputClassName}
            placeholder="Your name"
          />
        </label>
        <label className="grid gap-2 text-xs font-semibold">
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

      <label className="grid gap-2 text-xs font-semibold">
        What brings you in?
        <select
          required
          name="visit-type"
          className={inputClassName}
          defaultValue=""
        >
          <option value="" disabled>
            Choose one
          </option>
          <option>New patient visit</option>
          <option>Preventive visit</option>
          <option>Restorative care</option>
          <option>Cosmetic consultation</option>
          <option>Urgent concern</option>
        </select>
      </label>

      <fieldset>
        <legend className="flex items-center gap-2 text-xs font-semibold">
          <CalendarDays className="size-4 text-[#ff725e]" aria-hidden="true" />
          Choose an available date
        </legend>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {appointmentAvailability.map((day, index) => {
            const isSelected = index === selectedDayIndex;

            return (
              <button
                key={day.date}
                type="button"
                aria-pressed={isSelected}
                onClick={() => selectDay(index)}
                className={`rounded-xl border px-3 py-3 text-left transition-colors ${
                  isSelected
                    ? "border-[#173a5a] bg-[#173a5a] text-white"
                    : "border-[#173a5a]/14 bg-[#f3f7fb] text-[#173a5a]/60 hover:border-[#ff725e] hover:text-[#173a5a]"
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
          <Clock3 className="size-4 text-[#ff725e]" aria-hidden="true" />
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
                    ? "border-[#ff725e] bg-[#ff725e] text-white"
                    : "border-[#173a5a]/14 text-[#173a5a]/58 hover:border-[#ff725e] hover:text-[#173a5a]"
                }`}
              >
                {time}
              </button>
            );
          })}
        </div>
      </fieldset>

      <label className="grid gap-2 text-xs font-semibold">
        <span className="flex items-center gap-2">
          Anything we should know?
          <span className="font-normal text-[#173a5a]/42">Optional</span>
        </span>
        <textarea
          name="notes"
          rows={3}
          className={`${inputClassName} resize-y`}
          placeholder="Accessibility needs, symptoms, or a preferred provider."
        />
      </label>

      <div className="flex flex-col gap-2 rounded-2xl bg-[#dcebf6] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-[#173a5a]/42">
            Selected appointment
          </p>
          <p className="mt-1 text-sm font-semibold">
            {selectedDay.day}, {selectedDay.label} at {selectedTime}
          </p>
        </div>
        <p className="text-[10px] text-[#173a5a]/42">Demo availability</p>
      </div>

      <button
        type="submit"
        className="flex items-center justify-between rounded-full bg-[#ff725e] px-5 py-4 text-sm font-semibold text-white"
      >
        Request appointment
        <ArrowRight className="size-4" aria-hidden="true" />
      </button>
    </form>
  );
}
