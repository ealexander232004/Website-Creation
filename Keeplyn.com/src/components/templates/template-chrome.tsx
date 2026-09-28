import Image from "next/image";
import Link from "next/link";
import { ArrowDown, ArrowRight, ArrowUpRight, Menu, Plus } from "lucide-react";
import {
  businessHref,
  demoHref,
  demoSlugs,
  templates,
  type BusinessTemplate,
  type DemoPage,
  type DemoSlug,
  type TemplateImage,
} from "./catalog";
import { Contours, Glyph } from "./template-art";

export function Photo({
  image,
  className = "",
  eager = false,
  sizes = "(min-width: 900px) 50vw, 100vw",
}: {
  image: TemplateImage;
  className?: string;
  eager?: boolean;
  sizes?: string;
}) {
  return (
    <div className={`template-photo ${className}`}>
      <Image
        src={image.src}
        alt={image.alt}
        fill
        sizes={sizes}
        loading={eager ? "eager" : "lazy"}
        fetchPriority={eager ? "high" : "auto"}
      />
    </div>
  );
}

export function Brand({ business }: { business: BusinessTemplate }) {
  if (business.id === "moss")
    return (
      <span className="moss-wordmark">
        {business.wordmark?.[0] ?? business.name}
        {business.wordmark?.[1] && <span>{business.wordmark[1]}</span>}
      </span>
    );
  if (business.id === "northline")
    return (
      <span className="northline-wordmark">
        <Plus strokeWidth={3} aria-hidden="true" />
        {business.name.toLowerCase()}
      </span>
    );
  return (
    <span className="sera-wordmark">
      {business.name.toLowerCase()}
      <span>bakery &amp; coffee</span>
    </span>
  );
}

export function TemplateHeader({
  business: b,
  active = "home",
}: {
  business: BusinessTemplate;
  active?: DemoPage;
}) {
  const links = [
    ["about", b.nav.about],
    ["pricing", b.nav.pricing],
    ["faq", "FAQ"],
    ["contact", b.nav.contact],
  ] as const;
  return (
    <header className="template-header">
      <Link href={businessHref(b)} aria-label={`${b.name} home`}>
        <Brand business={b} />
      </Link>
      <nav className="template-desktop-nav" aria-label={`${b.name} navigation`}>
        {links.map(([page, label]) => (
          <Link
            key={page}
            href={businessHref(b, page)}
            aria-current={active === page ? "page" : undefined}
          >
            {label}
          </Link>
        ))}
      </nav>
      <Link className="template-header-cta" href={businessHref(b, "booking")}>
        {b.id === "sera"
          ? "Preorder"
          : b.id === "moss"
            ? "Start a project"
            : "Book a visit"}
        <ArrowUpRight size={16} aria-hidden="true" />
      </Link>
      <details className="template-mobile-menu">
        <summary aria-label={`Open ${b.name} menu`}>
          <Menu size={24} aria-hidden="true" />
        </summary>
        <nav aria-label={`${b.name} mobile navigation`}>
          <Link href={businessHref(b)}>Home</Link>
          {links.map(([page, label]) => (
            <Link
              key={page}
              href={businessHref(b, page)}
              aria-current={active === page ? "page" : undefined}
            >
              {label}
            </Link>
          ))}
          <Link href={businessHref(b, "booking")}>
            {b.action}
            <ArrowUpRight size={18} aria-hidden="true" />
          </Link>
        </nav>
      </details>
    </header>
  );
}

export function TemplateButton({
  business,
  page = "booking",
  children,
  light = false,
}: {
  business: BusinessTemplate;
  page?: DemoPage;
  children?: React.ReactNode;
  light?: boolean;
}) {
  return (
    <Link
      href={businessHref(business, page)}
      className={`template-button${light ? " is-light" : ""}`}
    >
      {children ?? business.action}
      <ArrowUpRight size={19} aria-hidden="true" />
    </Link>
  );
}

export function TemplateFooter({
  business: b,
}: {
  business: BusinessTemplate;
}) {
  return (
    <footer className="template-footer">
      {b.id === "moss" ? (
        <Contours className="template-footer-art" />
      ) : (
        <Glyph
          kind={b.id === "northline" ? "smile" : "croissant"}
          className="template-footer-art"
        />
      )}
      <div className="template-footer-top">
        <p>{b.closing}</p>
        <Link
          href={businessHref(b, "contact")}
          className="template-circle"
          aria-label={`Contact ${b.name}`}
        >
          <ArrowUpRight aria-hidden="true" />
        </Link>
      </div>
      <div className="template-footer-bottom">
        <Brand business={b} />
        <span>
          {b.location}
          <br />
          {b.hours}
        </span>
        <Link href={businessHref(b, "faq")}>
          A few good answers <ArrowRight size={16} aria-hidden="true" />
        </Link>
      </div>
      <div className="template-colophon">
        <span>
          © {new Date().getFullYear()} {b.name}
        </span>
        <span>
          A concept business · Website by <Link href="/">Keeplyn</Link>
        </span>
      </div>
    </footer>
  );
}

export function DemoToolbar({ active }: { active: DemoSlug }) {
  return (
    <div className="template-toolbar">
      <Link href="/demos" className="template-toolbar-back">
        <ArrowDown size={14} className="rotate-90" aria-hidden="true" />
        <strong>Keeplyn</strong>
        <span> / Demos</span>
      </Link>
      <nav aria-label="Switch demo website">
        {demoSlugs.map((id, i) => (
          <Link
            key={id}
            href={demoHref(id)}
            aria-current={active === id ? "page" : undefined}
          >
            <span>0{i + 1}</span> {templates[id].shortName}
          </Link>
        ))}
      </nav>
      <Link href="/start" className="template-toolbar-start">
        Make it yours <ArrowUpRight size={14} aria-hidden="true" />
      </Link>
    </div>
  );
}
