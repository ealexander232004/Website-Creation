import { ArrowDown, ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { BrandLogo } from "./brand-logo";

export function HeroSection() {
  return (
    <section className="relative min-h-[calc(100svh-68px)] overflow-hidden text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(5,5,5,0.42),transparent_48%)]" />

      <div className="site-container relative z-10 flex min-h-[calc(100svh-68px)] flex-col justify-between py-10 sm:py-14">
        <div className="reveal-on-load mx-auto mt-auto mb-auto max-w-6xl text-center">
          <h1 className="text-[clamp(3.6rem,9.5vw,9rem)] font-semibold leading-[0.82] tracking-[-0.085em]">
            The springboard{" "}
            <span className="block text-white/78">for your small business.</span>
          </h1>
          <div className="mt-10 flex flex-wrap justify-center gap-3">
            <Link href="/demos" className="button-primary">See the work</Link>
            <Link href="/contact" className="button-secondary">
              Start a project <ArrowUpRight className="size-4" aria-hidden="true" />
            </Link>
          </div>
        </div>

        <a href="#pricing" className="mx-auto flex w-fit items-center gap-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/40 hover:text-white">
          Plans <ArrowDown className="size-4 animate-bounce" aria-hidden="true" />
        </a>
      </div>
    </section>
  );
}

export function ContactSection() {
  return (
    <section id="contact" className="relative flex min-h-[calc(100svh-68px)] items-end overflow-hidden bg-[#050505] py-16 text-white sm:py-20">
      <div className="absolute -right-32 top-1/2 size-[38rem] -translate-y-1/2 rounded-full border border-[#7568ff]/35 shadow-[0_0_160px_rgba(117,104,255,0.24)]" aria-hidden="true" />
      <div className="absolute -right-10 top-1/2 size-[22rem] -translate-y-1/2 rounded-full border border-white/15" aria-hidden="true" />
      <div className="site-container relative z-10 w-full">
        <div className="max-w-6xl">
          <h1 className="text-[clamp(5.5rem,15vw,14rem)] font-semibold leading-[0.72] tracking-[-0.095em]">
            Let&apos;s build.
          </h1>
          <a
            href="mailto:hello@keeplyn.com?subject=Let%27s%20build%20my%20website"
            className="group mt-14 flex max-w-3xl items-center justify-between border-y border-white/20 py-6 text-lg font-medium transition-colors hover:border-[#c9ff3b] hover:text-[#c9ff3b] sm:text-3xl"
          >
            hello@keeplyn.com
            <ArrowUpRight className="size-6 transition-transform duration-300 group-hover:-translate-y-1 group-hover:translate-x-1" aria-hidden="true" />
          </a>
        </div>
      </div>
    </section>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-white/10 bg-[#050505] py-8 text-white">
      <div className="site-container flex flex-col justify-between gap-6 sm:flex-row sm:items-center">
          <BrandLogo inverse />
          <nav className="flex flex-wrap gap-x-7 gap-y-3 text-[10px] font-medium uppercase tracking-[0.14em] text-white/45" aria-label="Footer navigation">
            <Link href="/" className="hover:text-mint">Home</Link>
            <Link href="/pricing" className="hover:text-mint">Pricing</Link>
            <Link href="/demos" className="hover:text-mint">Demos</Link>
            <Link href="/contact" className="hover:text-mint">Contact</Link>
          </nav>
          <p className="text-[10px] text-white/30">© {new Date().getFullYear()}</p>
        </div>
    </footer>
  );
}
