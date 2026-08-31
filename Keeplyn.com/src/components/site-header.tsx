"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowUpRight, Menu, X } from "lucide-react";
import { BrandLogo } from "./brand-logo";

const navigation = [
  { label: "Home", href: "/" },
  { label: "Pricing", href: "/#pricing" },
  { label: "Demos", href: "/demos" },
  { label: "Contact", href: "/contact" },
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
    <header className="sticky top-0 z-50 border-b border-navy/15 bg-cream/95 backdrop-blur-xl">
      <div className="site-container flex h-[68px] items-center justify-between">
        <BrandLogo />

        <nav className="hidden items-center gap-8 lg:flex" aria-label="Main navigation">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-xs font-semibold uppercase tracking-[0.08em] text-slate transition-colors hover:text-navy"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2.5 sm:flex">
          <Link href="/contact" className="button-primary !px-4 !py-2.5">
            Get started
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </Link>
        </div>

        <div className="relative sm:hidden">
          <button
            type="button"
            className="grid size-10 place-items-center border border-navy/20 bg-transparent text-navy"
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
            <div className="absolute right-0 top-12 w-[min(19rem,calc(100vw-2rem))] border border-navy/15 bg-cream p-3 shadow-[0_24px_60px_rgba(21,21,21,0.14)]">
            <nav id="mobile-navigation" className="flex flex-col" aria-label="Mobile navigation">
              {navigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="px-4 py-3 text-sm font-semibold text-navy hover:bg-white"
                  onClick={() => setMobileOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
              <Link
                href="/contact"
                className="button-primary mt-2 justify-center"
                onClick={() => setMobileOpen(false)}
              >
                Get started
              </Link>
            </nav>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}
