import { ArrowUpRight, ChevronUp } from "lucide-react";
import Link from "next/link";

const policyLinks = [
  { label: "Terms of Service", href: "/terms-of-service" },
  { label: "Privacy Policy", href: "/privacy-policy" },
  {
    label: "Billing & Cancellation",
    href: "/billing-cancellation-policy",
  },
];

export function PoliciesMenu() {
  return (
    <div className="flex items-center gap-4 self-start sm:self-auto sm:justify-end">
      <p className="text-[10px] text-white/30">© {new Date().getFullYear()}</p>
      <details className="group/policies relative">
        <summary className="flex cursor-pointer list-none items-center gap-1.5 rounded-sm text-[10px] font-medium uppercase tracking-[0.14em] text-white/45 transition-colors hover:text-mint [&::-webkit-details-marker]:hidden">
          Terms &amp; Policies
          <ChevronUp
            className="size-3 transition-transform duration-200 group-open/policies:rotate-180"
            aria-hidden="true"
          />
        </summary>

        <nav
          aria-label="Terms and policies"
          className="pointer-events-none invisible absolute bottom-[calc(100%+0.85rem)] left-0 z-30 w-72 translate-y-2 rounded-lg border border-white/12 bg-[#101014]/98 p-2 opacity-0 shadow-[0_24px_70px_rgba(0,0,0,0.55)] backdrop-blur-xl transition duration-200 group-focus-within/policies:pointer-events-auto group-focus-within/policies:visible group-focus-within/policies:translate-y-0 group-focus-within/policies:opacity-100 group-hover/policies:pointer-events-auto group-hover/policies:visible group-hover/policies:translate-y-0 group-hover/policies:opacity-100 group-open/policies:pointer-events-auto group-open/policies:visible group-open/policies:translate-y-0 group-open/policies:opacity-100 sm:right-0 sm:left-auto"
        >
          <p className="px-3 pt-2 pb-2 text-[9px] font-semibold uppercase tracking-[0.18em] text-white/30">
            The fine print, plainly
          </p>
          <div className="space-y-1">
            {policyLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="group/link flex items-center justify-between rounded-md px-3 py-3 text-sm font-medium text-white/72 transition-colors hover:bg-white/7 hover:text-white focus-visible:bg-white/7 focus-visible:text-white"
              >
                {link.label}
                <ArrowUpRight
                  className="size-3.5 text-white/28 transition group-hover/link:-translate-y-0.5 group-hover/link:translate-x-0.5 group-hover/link:text-mint"
                  aria-hidden="true"
                />
              </Link>
            ))}
          </div>
        </nav>
      </details>
    </div>
  );
}
