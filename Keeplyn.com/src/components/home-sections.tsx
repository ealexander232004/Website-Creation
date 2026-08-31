import { ArrowRight, ArrowUpRight, Check } from "lucide-react";
import Link from "next/link";
import { BrandLogo } from "./brand-logo";

export function HeroSection() {
  return (
    <section className="overflow-hidden border-b border-navy/15 bg-cream py-16 sm:py-20 lg:py-24">
      <div className="site-container grid items-center gap-14 lg:grid-cols-[0.92fr_1.08fr] lg:gap-20">
        <div className="reveal-on-load">
          <p className="mb-7 font-mono text-[11px] uppercase tracking-[0.18em] text-violet">
            Independent web studio · California
          </p>
          <h1 className="max-w-3xl text-[3.25rem] font-semibold leading-[0.94] tracking-[-0.07em] text-navy sm:text-7xl lg:text-[5.35rem]">
            Websites that work hard
            <span className="block font-serif font-normal italic tracking-[-0.055em] text-violet">
              and look the part.
            </span>
          </h1>
          <p className="mt-8 max-w-xl text-base leading-7 text-slate sm:text-lg sm:leading-8">
            Strategy, design, development, and ongoing care for small businesses that have outgrown the starter site.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link href="/contact" className="button-primary justify-center sm:justify-start">
              Start a project
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </Link>
            <Link href="/demos" className="button-secondary justify-center sm:justify-start">
              Explore the demos
              <ArrowRight className="size-4" aria-hidden="true" />
            </Link>
          </div>
          <dl className="mt-12 grid max-w-xl grid-cols-3 border-y border-navy/15 py-4 text-xs">
            <div><dt className="text-slate">01</dt><dd className="mt-1 font-semibold text-navy">Strategy</dd></div>
            <div><dt className="text-slate">02</dt><dd className="mt-1 font-semibold text-navy">Design + build</dd></div>
            <div><dt className="text-slate">03</dt><dd className="mt-1 font-semibold text-navy">Care</dd></div>
          </dl>
        </div>

        <div className="hero-stage relative border border-navy/20 bg-[#d8ddce] p-3 shadow-[18px_18px_0_rgba(21,21,21,0.08)] sm:p-5">
          <div className="mb-3 flex items-center justify-between font-mono text-[9px] uppercase tracking-[0.12em] text-navy/55">
            <span>Selected concept / 01</span>
            <span>Live canvas</span>
          </div>
          <div className="hero-screen relative min-h-[30rem] overflow-hidden border border-navy/15 bg-[#eef0e7] p-6 shadow-[0_24px_60px_rgba(38,51,41,0.14)] sm:min-h-[36rem] sm:p-9">
            <div className="flex items-center justify-between border-b border-[#263329]/20 pb-5 text-[#263329]">
              <p className="text-sm font-semibold tracking-[-0.03em]">Moss &amp; Mortar</p>
              <div className="flex gap-5 text-[9px] font-semibold uppercase tracking-[0.1em]">
                <span>Work</span><span>Studio</span><span>Contact</span>
              </div>
            </div>
            <div className="grid min-h-[24rem] grid-cols-[1fr_0.38fr] gap-6 pt-10 sm:min-h-[29rem] sm:pt-14">
              <div className="flex flex-col justify-between">
                <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-[#263329]/55">Landscape design / Sacramento</p>
                <p className="max-w-md text-[2.7rem] font-semibold leading-[0.91] tracking-[-0.07em] text-[#263329] sm:text-[4rem]">
                  Outside,
                  <span className="block font-serif font-normal italic">considered.</span>
                </p>
                <p className="max-w-xs text-[11px] leading-5 text-[#263329]/60 sm:text-xs">
                  Thoughtful gardens and outdoor rooms made for Northern California living.
                </p>
              </div>
              <div className="relative border-l border-[#263329]/20">
                <div className="absolute inset-x-4 top-0 aspect-square bg-[#263329] shadow-[7px_7px_0_#aab69f]" />
                <p className="absolute bottom-0 left-4 font-mono text-[8px] uppercase tracking-[0.12em] text-[#263329]/55">Season 2026<br />Field notes</p>
              </div>
            </div>
            <span className="demo-cursor absolute grid size-8 place-items-center bg-mint text-[10px] font-bold text-navy shadow-[4px_4px_0_rgba(21,21,21,0.18)]" aria-hidden="true">↗</span>
          </div>
          <div className="mt-3 flex justify-between font-mono text-[9px] uppercase tracking-[0.12em] text-navy/55">
            <span>Brand / Web / Care</span>
            <span>Scroll to explore ↓</span>
          </div>
        </div>
      </div>
    </section>
  );
}

export function ContactSection() {
  return (
    <section id="contact" className="overflow-hidden bg-violet py-24 text-white sm:py-32">
      <div className="site-container" data-reveal>
        <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr] lg:items-start">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-mint">03 / Start here</p>
            <p className="mt-5 max-w-xs text-sm leading-7 text-white/65">
              Share the rough version. What you do, what feels stuck, and what the next version of the business needs.
            </p>
          </div>
          <div>
            <h2 className="text-5xl font-semibold leading-[0.92] tracking-[-0.07em] sm:text-7xl lg:text-[6.5rem]">
              Have a project
              <span className="block font-serif font-normal italic text-mint">in mind?</span>
            </h2>
            <a
              href="mailto:hello@keeplyn.com?subject=Let%27s%20build%20my%20website"
              className="group mt-14 flex items-center justify-between border-y border-white/35 py-6 text-xl font-semibold tracking-[-0.03em] transition-colors hover:border-mint hover:text-mint sm:text-3xl"
            >
              hello@keeplyn.com
              <ArrowUpRight className="size-7 transition-transform duration-300 group-hover:-translate-y-1 group-hover:translate-x-1" aria-hidden="true" />
            </a>
            <div className="mt-7 flex flex-wrap gap-x-8 gap-y-3 text-xs text-white/65">
              {["Clear next steps", "No-pressure conversation", "Straightforward scope"].map((item) => (
                <span key={item} className="flex items-center gap-2">
                  <Check className="size-3.5 text-mint" strokeWidth={3} aria-hidden="true" />
                  {item}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function SiteFooter() {
  return (
    <footer className="bg-navy py-10 text-white">
      <div className="site-container">
        <div className="flex flex-col justify-between gap-8 border-b border-white/15 pb-10 sm:flex-row sm:items-end">
          <div>
            <BrandLogo inverse />
            <p className="mt-4 max-w-sm text-sm leading-6 text-white/45">
              Strategy, design, development, and care for small businesses with somewhere to go.
            </p>
          </div>
          <nav className="flex flex-wrap gap-x-7 gap-y-3 font-mono text-[10px] uppercase tracking-[0.12em] text-white/55" aria-label="Footer navigation">
            <Link href="/" className="hover:text-mint">Home</Link>
            <Link href="/#pricing" className="hover:text-mint">Pricing</Link>
            <Link href="/demos" className="hover:text-mint">Demos</Link>
            <Link href="/contact" className="hover:text-mint">Contact</Link>
          </nav>
        </div>
        <div className="flex flex-col justify-between gap-3 pt-6 font-mono text-[9px] uppercase tracking-[0.1em] text-white/30 sm:flex-row sm:items-center">
          <p>© {new Date().getFullYear()} Keeplyn studio</p>
          <p>California / Working everywhere</p>
        </div>
      </div>
    </footer>
  );
}
