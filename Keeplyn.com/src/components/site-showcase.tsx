import Image from "next/image";
import Link from "next/link";
import { demoHref, templates, type DemoSlug } from "./templates/catalog";

// Screenshots from scripts/capture-demo-previews.mjs.
const previewHeights: Record<DemoSlug, number> = {
  moss: 3093,
  northline: 2433,
  sera: 2475,
};

export function BrowserFrame({
  slug,
  variant = "fold",
  sizes,
  eager = false,
  className = "",
}: {
  slug: DemoSlug;
  variant?: "fold" | "full";
  sizes: string;
  eager?: boolean;
  className?: string;
}) {
  const full = variant === "full";
  return (
    <div className={`browser-frame ${className}`}>
      <div className="browser-chrome" aria-hidden="true">
        <span className="browser-dots">
          <i />
          <i />
          <i />
        </span>
        <span className="browser-url">keeplyn.com/demos/{slug}</span>
      </div>
      <div className={`browser-viewport${full ? " is-scrolling" : ""}`}>
        <Image
          src={`/demos/previews/${slug}-${variant}.webp`}
          alt={`The ${templates[slug].name} homepage`}
          width={full ? 900 : 1440}
          height={full ? previewHeights[slug] : 900}
          sizes={sizes}
          loading={eager ? "eager" : "lazy"}
          fetchPriority={eager ? "high" : "auto"}
        />
      </div>
    </div>
  );
}

/** Three live demo sites fanned out beneath the homepage headline. */
export function HeroShowcase() {
  const order: DemoSlug[] = ["northline", "moss", "sera"];
  return (
    <div className="hero-showcase">
      {order.map((slug, i) => (
        <Link
          key={slug}
          href={demoHref(slug)}
          className={`hero-window hero-window-${i}`}
          aria-label={`Open the ${templates[slug].name} demo website`}
        >
          <BrowserFrame
            slug={slug}
            eager={i === 1}
            sizes="(min-width: 1024px) 46vw, 80vw"
          />
        </Link>
      ))}
    </div>
  );
}

/** Miniature product drawings for the Starter and Pro builds. */
export function PlanArt({
  plan,
  className = "",
}: {
  plan: "starter" | "pro";
  className?: string;
}) {
  const pro = plan === "pro";
  return (
    <svg
      className={`plan-art ${pro ? "is-pro" : ""} ${className}`}
      viewBox="0 0 440 170"
      fill="none"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={`plan-hero-${plan}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#7568ff" stopOpacity="0.85" />
          <stop offset="1" stopColor="#7568ff" stopOpacity="0.2" />
        </linearGradient>
        <radialGradient id="plan-orb" cx="0.35" cy="0.3" r="0.75">
          <stop offset="0" stopColor="#f7f7f4" />
          <stop offset="0.35" stopColor="#8b82ff" />
          <stop offset="1" stopColor="#2a2180" />
        </radialGradient>
      </defs>
      {/* Desktop window */}
      <g className="plan-art-window">
        <rect x="1" y="12" width="268" height="156" rx="10" className="plan-art-line" />
        <path d="M1 34H269" className="plan-art-line" />
        <circle cx="16" cy="23" r="3" className="plan-art-dot" />
        <circle cx="27" cy="23" r="3" className="plan-art-dot" />
        <circle cx="38" cy="23" r="3" className="plan-art-dot" />
        <rect x="14" y="46" width="242" height="58" rx="5" fill={`url(#plan-hero-${plan})`} />
        <rect x="26" y="62" width="92" height="9" rx="4.5" className="plan-art-fill" />
        <rect x="26" y="78" width="58" height="7" rx="3.5" className="plan-art-soft" />
        <rect x="14" y="114" width="74" height="42" rx="5" className="plan-art-line" />
        <rect x="98" y="114" width="74" height="42" rx="5" className="plan-art-line" />
        <rect x="182" y="114" width="74" height="42" rx="5" className="plan-art-line" />
      </g>
      {/* Phone */}
      <g className="plan-art-phone">
        <rect x="236" y="54" width="62" height="114" rx="11" className="plan-art-body" />
        <rect x="244" y="68" width="46" height="30" rx="4" fill={`url(#plan-hero-${plan})`} />
        <rect x="244" y="106" width="46" height="6" rx="3" className="plan-art-soft" />
        <rect x="244" y="118" width="32" height="6" rx="3" className="plan-art-soft" />
        <rect x="244" y="138" width="46" height="18" rx="9" className="plan-art-accent" />
      </g>
      {pro ? (
        <>
          {/* Payments */}
          <g className="plan-art-card">
            <rect x="318" y="96" width="112" height="70" rx="9" className="plan-art-body" />
            <rect x="318" y="112" width="112" height="12" className="plan-art-accent" />
            <rect x="330" y="140" width="40" height="7" rx="3.5" className="plan-art-soft" />
            <rect x="398" y="136" width="20" height="14" rx="3" className="plan-art-line" />
          </g>
          {/* Signed-in customer */}
          <g className="plan-art-user">
            <circle cx="330" cy="40" r="17" className="plan-art-body" />
            <circle cx="330" cy="35" r="6" className="plan-art-fill" />
            <path d="M319 50C321 43 339 43 341 50" className="plan-art-line" />
            <circle cx="344" cy="26" r="7" className="plan-art-accent" />
          </g>
          {/* 3D */}
          <circle cx="402" cy="44" r="26" fill="url(#plan-orb)" className="plan-art-orb" />
        </>
      ) : (
        <g className="plan-art-spark">
          <circle cx="360" cy="84" r="46" className="plan-art-ring" />
          <circle cx="360" cy="84" r="28" className="plan-art-ring" />
          <circle cx="360" cy="84" r="7" className="plan-art-accent" />
        </g>
      )}
    </svg>
  );
}
