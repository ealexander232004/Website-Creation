"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowUpRight, Menu, X } from "lucide-react";
import { BrandLogo } from "./brand-logo";

const navigation = [
  { label: "How it works", href: "#process" },
  { label: "Work", href: "#work" },
  { label: "Benefits", href: "#benefits" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
];

export function SiteHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setMobileOpen(false);
    }

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  return (
    <header className="sticky top-0 z-50 border-b border-navy/8 bg-cream/90 backdrop-blur-xl">
      <div className="site-container flex h-[72px] items-center justify-between">
        <BrandLogo />

        <nav className="hidden items-center gap-7 lg:flex" aria-label="Main navigation">
          {navigation.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="text-sm font-medium text-slate transition-colors hover:text-navy"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-2.5 sm:flex">
          <Link
            href="/login"
            className="rounded-xl px-4 py-2.5 text-sm font-semibold text-navy transition-colors hover:bg-navy/5"
          >
            Log in
          </Link>
          <a href="#contact" className="button-primary !px-4 !py-2.5">
            Get started
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </a>
        </div>

        <div className="relative sm:hidden">
          <button
            type="button"
            className="grid size-10 place-items-center rounded-xl border border-navy/10 bg-white text-navy shadow-sm"
            aria-label={mobileOpen ? "Close navigation" : "Open navigation"}
            aria-expanded={mobileOpen}
            aria-controls="mobile-navigation"
            onClick={() => setMobileOpen((open) => !open)}
          >
            {mobileOpen ? (
              <X className="size-5" aria-hidden="true" />
            ) : (
              <Menu className="size-5" aria-hidden="true" />
            )}
          </button>
          {mobileOpen ? (
            <div className="absolute right-0 top-12 w-[min(19rem,calc(100vw-2rem))] rounded-2xl border border-navy/10 bg-white p-3 shadow-2xl shadow-navy/12">
            <nav id="mobile-navigation" className="flex flex-col" aria-label="Mobile navigation">
              {navigation.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className="rounded-xl px-4 py-3 text-sm font-semibold text-navy hover:bg-mist"
                  onClick={() => setMobileOpen(false)}
                >
                  {item.label}
                </a>
              ))}
              <div className="my-2 h-px bg-navy/8" />
              <Link
                href="/login"
                className="rounded-xl px-4 py-3 text-sm font-semibold text-navy hover:bg-mist"
                onClick={() => setMobileOpen(false)}
              >
                Customer login
              </Link>
              <a
                href="#contact"
                className="button-primary mt-2 justify-center"
                onClick={() => setMobileOpen(false)}
              >
                Get started
              </a>
            </nav>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}
