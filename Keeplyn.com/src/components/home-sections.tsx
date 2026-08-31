import {
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Check,
  ClipboardCheck,
  Code2,
  Gauge,
  HeartHandshake,
  MessageSquareText,
  MonitorSmartphone,
  MousePointerClick,
  Palette,
  Search,
  ShieldCheck,
  Sparkles,
  WandSparkles,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { BrandLogo } from "./brand-logo";
import { SectionHeading } from "./section-heading";

const process = [
  {
    number: "01",
    icon: MessageSquareText,
    title: "Share your goals",
    description:
      "A focused kickoff uncovers what you offer, who you serve, and what your website needs to accomplish.",
  },
  {
    number: "02",
    icon: WandSparkles,
    title: "We design & build",
    description:
      "Keeplyn turns the strategy into a polished, responsive website—with clear checkpoints and no technical runaround.",
  },
  {
    number: "03",
    icon: ClipboardCheck,
    title: "Launch with confidence",
    description:
      "After a careful review, your website goes live. Choose ongoing care and we keep it healthy, current, and fast.",
  },
];

const benefits = [
  {
    icon: MousePointerClick,
    title: "Built to convert",
    description: "Clear hierarchy, purposeful calls to action, and pages that help visitors take the next step.",
  },
  {
    icon: MonitorSmartphone,
    title: "Excellent on every screen",
    description: "A mobile-first experience that feels considered on phones, tablets, laptops, and desktops.",
  },
  {
    icon: Gauge,
    title: "Fast by default",
    description: "Modern, lean technology that respects your customer’s time and supports search visibility.",
  },
  {
    icon: Palette,
    title: "Distinctly yours",
    description: "A cohesive visual direction shaped around your business—not a theme with your logo pasted in.",
  },
  {
    icon: Search,
    title: "Search-ready foundation",
    description: "Thoughtful page structure, metadata, and technical essentials built in from the start.",
  },
  {
    icon: HeartHandshake,
    title: "Human support",
    description: "Direct, plain-English communication from kickoff through launch and ongoing care.",
  },
];

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-cream pb-20 pt-12 sm:pb-28 sm:pt-18 lg:pb-32 lg:pt-24">
      <div className="hero-grid absolute inset-x-0 top-0 h-[32rem] opacity-50 [mask-image:linear-gradient(to_bottom,black,transparent)]" />
      <div className="absolute -left-36 top-32 size-80 rounded-full bg-mint/25 blur-[90px]" />
      <div className="absolute -right-40 top-0 size-96 rounded-full bg-violet/12 blur-[100px]" />

      <div className="site-container relative grid items-center gap-16 lg:grid-cols-[0.93fr_1.07fr] lg:gap-12">
        <div>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet/15 bg-white/75 px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.13em] text-violet shadow-sm backdrop-blur">
            <Sparkles className="size-3.5" aria-hidden="true" />
            Websites for ambitious small businesses
          </div>
          <h1 className="max-w-3xl text-balance text-[2.8rem] font-bold leading-[0.98] tracking-[-0.065em] text-navy sm:text-6xl lg:text-[4.65rem]">
            A better website for the business you’re building.
          </h1>
          <p className="mt-7 max-w-xl text-pretty text-lg leading-8 text-slate sm:text-xl">
            Keeplyn creates modern, high-performing websites that make small businesses look established, earn trust, and turn more visits into real inquiries.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <a href="#contact" className="button-primary justify-center sm:justify-start">
              Start your website
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </a>
            <a href="#work" className="button-secondary justify-center sm:justify-start">
              Explore the work
              <ArrowRight className="size-4" aria-hidden="true" />
            </a>
          </div>
          <ul className="mt-8 flex flex-wrap gap-x-5 gap-y-3 text-xs font-semibold text-slate" aria-label="Keeplyn service highlights">
            {[
              "Straightforward pricing",
              "Custom responsive design",
              "Ongoing care available",
            ].map((item) => (
              <li key={item} className="flex items-center gap-2">
                <span className="grid size-5 place-items-center rounded-full bg-mint text-navy">
                  <Check className="size-3" strokeWidth={3} aria-hidden="true" />
                </span>
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative mx-auto w-full max-w-[42rem] lg:ml-auto">
          <div className="absolute -inset-5 rotate-2 rounded-[2.25rem] bg-violet/8" />
          <div className="relative overflow-hidden rounded-[1.75rem] border border-navy/10 bg-white p-2.5 shadow-[0_36px_90px_-32px_rgba(15,23,42,0.35)] sm:p-3">
            <div className="overflow-hidden rounded-[1.25rem] border border-navy/8 bg-[#e1e9dd]">
              <div className="flex h-10 items-center gap-1.5 border-b border-navy/8 bg-white/75 px-4 backdrop-blur">
                <span className="size-2 rounded-full bg-[#ff8585]" />
                <span className="size-2 rounded-full bg-[#ffd16c]" />
                <span className="size-2 rounded-full bg-[#72d69b]" />
                <div className="mx-auto flex h-5 w-1/2 items-center justify-center rounded-md bg-navy/5 text-[7px] font-medium text-navy/35">
                  mossandmortar.demo
                </div>
              </div>
              <div className="relative min-h-[23rem] overflow-hidden p-5 sm:p-7">
                <div className="absolute -right-10 top-12 size-52 rounded-full border-[28px] border-white/18" />
                <div className="absolute -bottom-32 -left-14 size-72 rounded-full bg-[#9eaf8f]/50" />
                <div className="relative flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#29382b]">
                    <span className="grid size-7 place-items-center rounded-full bg-[#29382b] text-[8px] text-white">M&M</span>
                    Moss & Mortar
                  </div>
                  <div className="hidden items-center gap-5 text-[9px] font-semibold text-[#29382b]/60 sm:flex">
                    <span>Services</span>
                    <span>About</span>
                    <span className="rounded-full bg-[#29382b] px-3 py-1.5 text-white">Get a quote</span>
                  </div>
                </div>
                <div className="relative mt-16 max-w-sm sm:mt-20">
                  <p className="mb-3 text-[9px] font-bold uppercase tracking-[0.2em] text-[#4b654e]">Landscape design & care</p>
                  <p className="text-[2.35rem] font-bold leading-[0.95] tracking-[-0.065em] text-[#29382b] sm:text-[3.1rem]">
                    Outdoor spaces, thoughtfully grown.
                  </p>
                  <p className="mt-4 max-w-[17rem] text-[10px] leading-4 text-[#29382b]/60 sm:text-xs sm:leading-5">
                    Intentional landscapes designed for the way you live—beautiful in every season.
                  </p>
                </div>
                <div className="absolute bottom-5 right-5 grid size-28 place-items-center rounded-[1.5rem] bg-[#29382b] shadow-xl sm:size-36">
                  <svg aria-hidden="true" viewBox="0 0 120 120" className="size-24 sm:size-28">
                    <path d="M24 97c15-26 21-49 18-74 18 15 30 35 31 58 2-19 10-34 23-45 2 27-9 49-31 63" fill="none" stroke="#dce9d8" strokeWidth="3" strokeLinecap="round" />
                    <path d="M42 45c-11 3-18 10-22 20M49 60c-10 4-16 11-19 20M78 62c9 2 15 7 18 15" fill="none" stroke="#a7c3a4" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <div className="absolute -bottom-8 -left-3 rounded-2xl border border-navy/10 bg-white p-4 shadow-xl shadow-navy/10 sm:-left-8 sm:p-5">
            <div className="flex items-center gap-3">
              <span className="grid size-9 place-items-center rounded-xl bg-mint text-navy">
                <Zap className="size-4" fill="currentColor" aria-hidden="true" />
              </span>
              <div>
                <p className="text-xs font-bold text-navy">Fast & responsive</p>
                <p className="mt-0.5 text-[10px] text-slate">Built for every screen</p>
              </div>
            </div>
          </div>
          <div className="absolute -right-3 -top-7 hidden rounded-2xl border border-white/20 bg-navy p-4 text-white shadow-xl shadow-navy/20 sm:block">
            <div className="flex items-center gap-3">
              <BarChart3 className="size-5 text-mint" aria-hidden="true" />
              <div>
                <p className="text-xs font-bold">Clear next steps</p>
                <p className="mt-0.5 text-[10px] text-white/45">Designed to convert</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function ProcessSection() {
  return (
    <section id="process" className="section-space bg-white">
      <div className="site-container">
        <div className="flex flex-col justify-between gap-7 lg:flex-row lg:items-end">
          <SectionHeading
            eyebrow="Simple by design"
            title="From first conversation to a confident launch."
            description="A clear process keeps the project moving and gives you room to focus on your business."
          />
          <a href="#pricing" className="group inline-flex items-center gap-2 text-sm font-bold text-navy">
            See straightforward pricing
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
          </a>
        </div>

        <div className="relative mt-12 grid gap-5 lg:grid-cols-3">
          <div className="absolute left-[16%] right-[16%] top-12 hidden border-t border-dashed border-violet/25 lg:block" />
          {process.map((step) => {
            const Icon = step.icon;
            return (
              <article key={step.number} className="relative rounded-[1.5rem] border border-navy/8 bg-cream p-6 sm:p-8">
                <div className="relative flex items-center justify-between">
                  <span className="grid size-12 place-items-center rounded-2xl bg-navy text-mint shadow-lg shadow-navy/12">
                    <Icon className="size-5" aria-hidden="true" />
                  </span>
                  <span className="font-mono text-xs font-bold text-violet">{step.number}</span>
                </div>
                <h3 className="mt-8 text-xl font-bold tracking-[-0.035em] text-navy">{step.title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate">{step.description}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export function BenefitsSection() {
  return (
    <section id="benefits" className="section-space bg-cream">
      <div className="site-container">
        <SectionHeading
          eyebrow="Why Keeplyn"
          title="Good design is only the beginning."
          description="Your website should look polished, load quickly, explain your value, and make it easy for the right customer to reach you."
          align="center"
        />
        <div className="mt-12 grid gap-px overflow-hidden rounded-[1.75rem] border border-navy/8 bg-navy/8 sm:grid-cols-2 lg:grid-cols-3">
          {benefits.map((benefit) => {
            const Icon = benefit.icon;
            return (
              <article key={benefit.title} className="group bg-white p-7 transition-colors hover:bg-mist sm:p-8">
                <span className="grid size-11 place-items-center rounded-2xl bg-violet/8 text-violet transition-all group-hover:-rotate-3 group-hover:bg-violet group-hover:text-white">
                  <Icon className="size-5" aria-hidden="true" />
                </span>
                <h3 className="mt-6 text-lg font-bold tracking-[-0.03em] text-navy">{benefit.title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate">{benefit.description}</p>
              </article>
            );
          })}
        </div>
        <div className="mt-7 flex flex-col items-start justify-between gap-5 rounded-2xl bg-navy px-6 py-5 text-white sm:flex-row sm:items-center sm:px-8">
          <div className="flex items-start gap-4 sm:items-center">
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-mint text-navy">
              <ShieldCheck className="size-5" aria-hidden="true" />
            </span>
            <div>
              <p className="font-bold">Modern foundations, fewer headaches.</p>
              <p className="mt-1 text-sm text-white/55">Built with maintainable technology and supported in plain English.</p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2 text-xs font-semibold text-mint">
            <Code2 className="size-4" aria-hidden="true" />
            Next.js powered
          </div>
        </div>
      </div>
    </section>
  );
}

export function ContactSection() {
  return (
    <section id="contact" className="relative overflow-hidden bg-violet py-20 text-white sm:py-28">
      <div className="absolute -left-16 -top-32 size-80 rounded-full border-[55px] border-white/5" />
      <div className="absolute -bottom-36 -right-16 size-96 rounded-full bg-mint/15 blur-[2px]" />
      <div className="site-container relative grid items-center gap-10 lg:grid-cols-[1fr_auto]">
        <div className="max-w-3xl">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-mint">Ready when you are</p>
          <h2 className="mt-5 text-balance text-4xl font-bold tracking-[-0.055em] sm:text-5xl lg:text-6xl">
            Let’s build the website your business deserves.
          </h2>
          <p className="mt-6 max-w-xl text-pretty text-base leading-7 text-white/65 sm:text-lg">
            Tell us what you’re building, what is not working today, and where you want to go next. You’ll get a clear response—not a hard sell.
          </p>
          <div className="mt-8 flex flex-wrap gap-x-6 gap-y-3 text-xs font-semibold text-white/70">
            {["Clear next steps", "No-pressure conversation", "Straightforward scope"].map((item) => (
              <span key={item} className="flex items-center gap-2">
                <Check className="size-4 text-mint" strokeWidth={3} aria-hidden="true" />
                {item}
              </span>
            ))}
          </div>
        </div>
        <a
          href="mailto:hello@keeplyn.com?subject=Let%27s%20build%20my%20website"
          className="group flex w-full items-center justify-between gap-6 rounded-2xl bg-white p-5 text-navy shadow-2xl shadow-navy/15 transition-transform hover:-translate-y-1 sm:w-auto sm:min-w-72"
        >
          <div>
            <span className="block text-[10px] font-bold uppercase tracking-[0.16em] text-violet">Start a conversation</span>
            <span className="mt-1.5 block text-lg font-bold">hello@keeplyn.com</span>
          </div>
          <span className="grid size-11 place-items-center rounded-xl bg-mint transition-transform group-hover:rotate-6">
            <ArrowUpRight className="size-5" aria-hidden="true" />
          </span>
        </a>
      </div>
    </section>
  );
}

export function SiteFooter() {
  return (
    <footer className="bg-navy py-10 text-white">
      <div className="site-container">
        <div className="flex flex-col justify-between gap-8 border-b border-white/10 pb-8 sm:flex-row sm:items-center">
          <div>
            <BrandLogo inverse />
            <p className="mt-3 max-w-sm text-sm leading-6 text-white/45">
              Modern websites for small businesses ready to look established and grow with confidence.
            </p>
          </div>
          <nav className="flex flex-wrap gap-x-6 gap-y-3 text-xs font-semibold text-white/60" aria-label="Footer navigation">
            <a href="#process" className="hover:text-white">Process</a>
            <a href="#work" className="hover:text-white">Work</a>
            <a href="#pricing" className="hover:text-white">Pricing</a>
            <a href="#faq" className="hover:text-white">FAQ</a>
            <Link href="/login" className="hover:text-white">Login</Link>
          </nav>
        </div>
        <div className="flex flex-col justify-between gap-3 pt-6 text-[11px] text-white/30 sm:flex-row sm:items-center">
          <p>© {new Date().getFullYear()} Keeplyn. Built with care.</p>
          <p>Web design · Hosting · Ongoing care</p>
        </div>
      </div>
    </footer>
  );
}
