import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { BrandLogo } from "./brand-logo";
import { ContactInquiryForm } from "./contact-inquiry-form";
import { PoliciesMenu } from "./policies-menu";

export function HeroSection() {
  return (
    <section className="relative min-h-[calc(100svh-68px)] overflow-hidden text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(5,5,5,0.42),transparent_48%)]" />

      <div className="site-container relative z-10 flex min-h-[calc(100svh-68px)] flex-col justify-between py-10 sm:py-14">
        <div className="reveal-on-load mx-auto mt-auto mb-auto max-w-6xl text-center">
          <h1 className="text-[clamp(3.6rem,9.5vw,9rem)] font-semibold leading-[0.82] tracking-[-0.085em]">
            <span className="text-white/78">The </span>springboard{" "}
            <span className="block text-white/78">for your small business.</span>
          </h1>
          <p className="hero-subtitle-shimmer mt-7 text-[clamp(1rem,1.6vw,1.35rem)] font-medium tracking-[-0.02em]">
            Professional, customized websites
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/demos" className="button-primary">View demos</Link>
            <Link href="/start" className="button-secondary">
              Start a project <ArrowUpRight className="size-4" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

export function ContactSection() {
  return (
    <section id="contact" className="relative overflow-hidden bg-[#050505] py-16 text-white sm:py-24">
      <div className="absolute -left-32 top-1/2 size-[38rem] -translate-y-1/2 rounded-full border border-[#7568ff]/35 shadow-[0_0_160px_rgba(117,104,255,0.24)]" aria-hidden="true" />
      <div className="absolute -left-10 top-1/2 size-[22rem] -translate-y-1/2 rounded-full border border-white/15" aria-hidden="true" />
      <div className="site-container relative z-10 w-full">
        <div className="grid min-h-[calc(100svh-68px-8rem)] items-center gap-14 lg:grid-cols-[1.05fr_.95fr] lg:gap-20">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9ff3b]">
              General inquiries
            </p>
            <h1 className="mt-5 max-w-4xl text-[clamp(4.5rem,10vw,9rem)] font-semibold leading-[0.78] tracking-[-0.09em]">
              Let&apos;s talk.
            </h1>
            <p className="mt-8 max-w-lg text-base leading-7 text-white/48">
              Have a question about Keeplyn? Send us a note. If you&apos;re ready to request a website,
              use the guided project flow instead.
            </p>
            <Link href="/start" className="button-secondary mt-7">
              Get started
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </Link>
          </div>

          <ContactInquiryForm />
        </div>
      </div>
    </section>
  );
}

export function SiteFooter() {
  return (
    <footer className="relative z-20 border-t border-white/10 bg-[#050505] py-8 text-white">
      <div className="site-container flex flex-col justify-between gap-6 sm:flex-row sm:items-center">
        <BrandLogo />
        <nav className="flex flex-wrap gap-x-7 gap-y-3 text-[10px] font-medium uppercase tracking-[0.14em] text-white/45" aria-label="Footer navigation">
          <Link href="/" className="transition-colors hover:text-mint">Home</Link>
          <Link href="/pricing" className="transition-colors hover:text-mint">Pricing</Link>
          <Link href="/demos" className="transition-colors hover:text-mint">Demos</Link>
          <Link href="/contact" className="transition-colors hover:text-mint">Contact</Link>
        </nav>
        <PoliciesMenu />
      </div>
    </footer>
  );
}
