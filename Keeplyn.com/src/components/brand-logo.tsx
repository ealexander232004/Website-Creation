import Link from "next/link";

interface BrandLogoProps {
  inverse?: boolean;
}

export function BrandLogo({ inverse = false }: BrandLogoProps) {
  return (
    <Link
      href="/"
      className="group inline-flex items-center gap-2.5"
      aria-label="Keeplyn home"
    >
      <span
        className={`grid size-8 place-items-center border transition-transform duration-300 group-hover:-translate-y-0.5 ${
          inverse
            ? "border-white/15 bg-white/10"
            : "border-navy/10 bg-navy"
        }`}
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          className="size-[1.1rem]"
          fill="none"
        >
          <path
            d="M7 5v14M18 5l-8.5 8.25M11.5 11.25 18.5 19"
            stroke={inverse ? "#BDFBE8" : "#BDFBE8"}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <span
        className={`text-base font-semibold tracking-[-0.035em] ${
          inverse ? "text-white" : "text-navy"
        }`}
      >
        Keeplyn<span className="text-violet">/</span>
      </span>
    </Link>
  );
}
