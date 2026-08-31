"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowRight, ArrowUpRight, CalendarDays, Clock3, MapPin } from "lucide-react";
import { useRef, useState, type KeyboardEvent } from "react";

const demoTabs = [
  { id: "moss", name: "Moss & Mortar", type: "Landscape studio", href: "/demos/moss" },
  { id: "northline", name: "Northline", type: "Family dentistry", href: "/demos/northline" },
  { id: "sera", name: "Sera", type: "Neighborhood bakery", href: "/demos/sera" },
] as const;

export function MossSite() {
  return (
    <div className="bg-[#dfe5d6] text-[#203126]">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[#203126]/20 px-5 py-5 sm:px-9">
        <Link href="/demos/moss" className="text-lg font-semibold tracking-[-0.04em]">Moss &amp; Mortar</Link>
        <nav className="order-3 flex w-full gap-6 text-[10px] font-semibold uppercase tracking-[0.14em] sm:order-none sm:w-auto sm:gap-7" aria-label="Moss & Mortar demo navigation">
          <a href="#moss-work">Work</a><Link href="/demos/moss/pricing">Pricing</Link><Link href="/demos/moss/contact">Contact</Link>
        </nav>
        <Link href="/demos/moss/contact" className="border border-[#203126] px-4 py-2 text-xs font-semibold">Start a garden</Link>
      </header>

      <section id="moss-top" className="grid min-h-[48rem] lg:grid-cols-[0.48fr_0.52fr]">
        <div className="flex flex-col p-6 sm:p-10 lg:p-14">
          <div className="my-auto py-20">
            <h2 className="text-[clamp(4rem,9vw,8.8rem)] font-semibold leading-[0.78] tracking-[-0.085em]">
              Outside,
              <span className="block font-serif font-normal italic">considered.</span>
            </h2>
            <p className="mt-8 max-w-md text-base leading-7 text-[#203126]/66">
              Gardens, courtyards, and outdoor rooms designed around the way you actually live.
            </p>
          </div>
          <a href="#moss-work" className="flex items-center justify-between border-t border-[#203126]/25 pt-5 text-sm font-semibold">
            Explore selected work <ArrowRight className="size-4" aria-hidden="true" />
          </a>
        </div>
        <div className="relative min-h-[36rem] overflow-hidden">
          <Image src="/demos/moss-garden.jpg" alt="Lush modern courtyard garden" fill sizes="(min-width: 1024px) 52vw, 100vw" className="object-cover" preload />
          <div className="absolute inset-0 bg-gradient-to-t from-[#203126]/28 via-transparent to-transparent" />
          <div className="absolute bottom-6 left-6 border border-white/35 bg-black/20 px-4 py-3 text-xs text-white backdrop-blur-md">Courtyard No. 08 · 2026</div>
        </div>
      </section>

      <div className="grid border-y border-[#203126]/20 sm:grid-cols-3 sm:divide-x sm:divide-[#203126]/20">
        {[['18', 'gardens completed'], ['11', 'native plant palettes'], ['07', 'design awards']].map(([value, label]) => (
          <div key={label} className="p-7 sm:p-9">
            <p className="text-5xl font-semibold tracking-[-0.07em]">{value}</p>
            <p className="mt-2 text-xs text-[#203126]/55">{label}</p>
          </div>
        ))}
      </div>

      <section id="moss-work" className="px-6 py-24 sm:px-10 lg:px-14 lg:py-32">
        <div className="flex items-end justify-between gap-8 border-b border-[#203126]/20 pb-6">
          <h3 className="text-4xl font-semibold tracking-[-0.06em] sm:text-6xl">Selected ground.</h3>
          <span className="text-[10px] uppercase tracking-[0.16em] text-[#203126]/45">2024—2026</span>
        </div>
        <div className="mt-8 grid gap-5 lg:grid-cols-3">
          {[
            ["River House", "A shaded family garden built around a 70-year-old oak.", "#a8b99b"],
            ["South Slope", "Dry-climate terraces that get better with every season.", "#c4c6a1"],
            ["Night Garden", "A small urban courtyard shaped by scent, sound, and low light.", "#708174"],
          ].map(([name, detail, color], index) => (
            <article key={name} className="group flex min-h-[28rem] flex-col justify-between overflow-hidden p-6" style={{ background: color }}>
              <div className="relative h-44 overflow-hidden border border-[#203126]/15">
                <div className="absolute -right-10 -top-12 size-52 rounded-full border border-[#203126]/35 transition-transform duration-700 group-hover:scale-125" />
                <div className="absolute bottom-6 left-6 size-20 rounded-full bg-[#203126]/85 transition-transform duration-700 group-hover:translate-x-8" />
                <span className="absolute right-4 top-4 text-[10px]">0{index + 1}</span>
              </div>
              <div>
                <h4 className="text-3xl font-semibold tracking-[-0.055em]">{name}</h4>
                <p className="mt-3 max-w-xs text-sm leading-6 text-[#203126]/62">{detail}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section id="moss-approach" className="grid border-y border-[#203126]/20 bg-[#203126] text-[#edf1e9] lg:grid-cols-2">
        <div className="p-7 sm:p-12 lg:p-16">
          <p className="text-[10px] uppercase tracking-[0.16em] text-[#c9ff3b]">Our approach</p>
          <h3 className="mt-10 text-5xl font-semibold leading-[0.9] tracking-[-0.07em] sm:text-7xl">Start with the life. Then shape the land.</h3>
        </div>
        <ol className="divide-y divide-white/15 border-t border-white/15 lg:border-t-0 lg:border-l">
          {[
            ["01", "Listen", "We map the rituals, constraints, and seasons that matter."],
            ["02", "Compose", "Materials, plants, light, water, and movement become one system."],
            ["03", "Grow", "We stay through installation and the garden's first year."],
          ].map(([number, title, detail]) => (
            <li key={number} className="grid grid-cols-[3rem_1fr] gap-4 p-7 sm:p-10">
              <span className="text-xs text-white/35">{number}</span>
              <div><h4 className="text-xl font-semibold">{title}</h4><p className="mt-2 text-sm leading-6 text-white/52">{detail}</p></div>
            </li>
          ))}
        </ol>
      </section>

      <section id="moss-contact" className="px-6 py-24 sm:px-10 lg:px-14 lg:py-32">
        <p className="text-[10px] uppercase tracking-[0.16em] text-[#203126]/45">Now booking autumn 2026</p>
        <Link href="/demos/moss/contact" className="group mt-6 flex items-end justify-between border-y border-[#203126]/20 py-8">
          <span className="text-5xl font-semibold tracking-[-0.07em] sm:text-8xl">Grow something lasting.</span>
          <ArrowUpRight className="mb-2 size-9 transition-transform group-hover:-translate-y-2 group-hover:translate-x-2" aria-hidden="true" />
        </Link>
      </section>

      <footer className="flex flex-col justify-between gap-4 border-t border-[#203126]/20 px-6 py-7 text-xs text-[#203126]/52 sm:flex-row sm:px-10 lg:px-14">
        <span>Moss &amp; Mortar Landscape Studio</span><Link href="/demos">All demos</Link><span>© 2026</span>
      </footer>
    </div>
  );
}

export function NorthlineSite() {
  return (
    <div className="bg-[#f3f7fb] text-[#173a5a]">
      <header className="flex flex-wrap items-center justify-between gap-4 px-5 py-5 sm:px-9">
        <Link href="/demos/northline" className="text-lg font-semibold tracking-[-0.04em]">northline<span className="text-[#ff725e]">●</span></Link>
        <nav className="order-3 flex w-full gap-6 text-[10px] font-semibold uppercase tracking-[0.13em] md:order-none md:w-auto md:gap-7" aria-label="Northline demo navigation">
          <a href="#northline-services">Services</a><Link href="/demos/northline/pricing">Pricing</Link><Link href="/demos/northline/contact">Contact</Link>
        </nav>
        <Link href="/demos/northline/contact" className="rounded-full bg-[#173a5a] px-5 py-2.5 text-xs font-semibold text-white">Book a visit</Link>
      </header>

      <section id="northline-top" className="px-5 pb-8 sm:px-9">
        <div className="relative min-h-[46rem] overflow-hidden rounded-[2rem] bg-[#bfd9ef]">
          <Image src="/demos/northline-clinic.jpg" alt="Dentist speaking with a patient in a modern clinic" fill sizes="100vw" className="object-cover object-center" preload />
          <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(23,58,90,.88)_0%,rgba(23,58,90,.46)_42%,rgba(23,58,90,.05)_72%)]" />
          <div className="absolute inset-x-0 bottom-0 p-7 text-white sm:p-12 lg:p-16">
            <h2 className="max-w-4xl text-[clamp(4rem,9vw,8.6rem)] font-semibold leading-[0.82] tracking-[-0.085em]">
              Care, without the rush.
            </h2>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/demos/northline/contact" className="rounded-full bg-[#ff725e] px-6 py-3 text-sm font-semibold text-white">New patient visit</Link>
              <a href="#northline-services" className="rounded-full border border-white/45 bg-white/10 px-6 py-3 text-sm font-semibold backdrop-blur-md">See our care</a>
            </div>
          </div>
        </div>
      </section>

      <section id="northline-services" className="px-6 py-24 sm:px-10 lg:px-14 lg:py-32">
        <div className="grid gap-12 lg:grid-cols-[0.34fr_0.66fr]">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#ff725e]">Whole-person dentistry</p>
            <h3 className="mt-5 text-4xl font-semibold leading-[0.96] tracking-[-0.06em] sm:text-5xl">Everything your smile needs. Nothing it doesn&apos;t.</h3>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              ["01", "Everyday care", "Exams, cleanings, fillings, and practical prevention."],
              ["02", "Restorative", "Natural-looking crowns, bridges, and implant restoration."],
              ["03", "Cosmetic", "Whitening and subtle changes planned around your face."],
            ].map(([number, title, detail]) => (
              <article key={number} className="rounded-[1.5rem] border border-[#173a5a]/12 bg-white p-6 shadow-[0_18px_50px_rgba(23,58,90,.08)]">
                <span className="grid size-9 place-items-center rounded-full bg-[#dbeaf6] text-xs font-semibold">{number}</span>
                <h4 className="mt-16 text-xl font-semibold tracking-[-0.035em]">{title}</h4>
                <p className="mt-3 text-sm leading-6 text-[#173a5a]/58">{detail}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="northline-visit" className="mx-5 overflow-hidden rounded-[2rem] bg-[#173a5a] text-white sm:mx-9">
        <div className="grid lg:grid-cols-[0.45fr_0.55fr]">
          <div className="p-7 sm:p-12 lg:p-16">
            <p className="text-[10px] uppercase tracking-[0.16em] text-[#ffb0a3]">Your first visit</p>
            <h3 className="mt-6 text-5xl font-semibold leading-[0.9] tracking-[-0.07em] sm:text-7xl">Clear from the start.</h3>
            <p className="mt-6 max-w-md text-sm leading-7 text-white/58">We leave room for questions, explain every option, and never turn a conversation into a sales pitch.</p>
          </div>
          <ol className="divide-y divide-white/14 border-t border-white/14 lg:border-t-0 lg:border-l">
            {[
              ["01", "Talk first", "Tell us what feels good, what doesn't, and what you want next."],
              ["02", "Look together", "Digital imaging and a gentle exam, explained in real time."],
              ["03", "Leave with a plan", "Priorities, timing, and cost—written in plain language."],
            ].map(([number, title, detail]) => (
              <li key={number} className="grid grid-cols-[3rem_1fr] gap-4 p-7 sm:p-10">
                <span className="text-xs text-[#ff8f7d]">{number}</span>
                <div><h4 className="text-xl font-semibold">{title}</h4><p className="mt-2 text-sm leading-6 text-white/55">{detail}</p></div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section id="northline-contact" className="px-6 py-24 sm:px-10 lg:px-14 lg:py-32">
        <div className="grid gap-10 lg:grid-cols-[0.62fr_0.38fr] lg:items-end">
          <div>
            <p className="text-[10px] uppercase tracking-[0.16em] text-[#ff725e]">Accepting new patients</p>
            <h3 className="mt-5 text-5xl font-semibold leading-[0.9] tracking-[-0.07em] sm:text-8xl">Your calmer visit starts here.</h3>
          </div>
          <div className="rounded-[1.5rem] border border-[#173a5a]/12 bg-white p-6">
            <div className="flex items-center gap-3 border-b border-[#173a5a]/12 pb-4"><CalendarDays className="size-5 text-[#ff725e]" /><span className="text-sm font-semibold">Next available</span></div>
            <p className="mt-7 text-4xl font-semibold tracking-[-0.06em]">Tuesday 14</p>
            <p className="mt-2 text-sm text-[#173a5a]/55">9:30am · New patient exam</p>
            <Link href="/demos/northline/contact" className="mt-8 flex items-center justify-between rounded-full bg-[#ff725e] px-5 py-3 text-sm font-semibold text-white">Request this time <ArrowRight className="size-4" /></Link>
          </div>
        </div>
      </section>

      <footer className="flex flex-col justify-between gap-5 bg-[#dcebf6] px-6 py-8 text-xs sm:flex-row sm:items-center sm:px-10 lg:px-14">
        <span className="text-base font-semibold">northline<span className="text-[#ff725e]">●</span></span><Link href="/demos">All demos</Link><span>(510) 555-0144</span>
      </footer>
    </div>
  );
}

export function SeraSite() {
  return (
    <div className="bg-[#f6e8d8] text-[#5d2d26]">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[#5d2d26]/18 px-5 py-5 sm:px-9">
        <Link href="/demos/sera" className="font-serif text-3xl italic">Sera</Link>
        <nav className="order-3 flex w-full gap-6 text-[10px] font-semibold uppercase tracking-[0.14em] sm:order-none sm:w-auto sm:gap-7" aria-label="Sera demo navigation">
          <a href="#sera-menu">Menu</a><Link href="/demos/sera/pricing">Pricing</Link><Link href="/demos/sera/contact">Contact</Link>
        </nav>
        <p className="text-[10px] font-semibold uppercase tracking-[0.13em]">Open 7—2</p>
      </header>

      <section id="sera-top" className="grid min-h-[48rem] lg:grid-cols-2">
        <div className="relative min-h-[34rem] overflow-hidden lg:order-2">
          <Image src="/demos/sera-bread.jpg" alt="Freshly baked artisan bread on display" fill sizes="(min-width: 1024px) 50vw, 100vw" className="object-cover" preload />
          <div className="absolute inset-0 bg-gradient-to-t from-[#5d2d26]/28 to-transparent" />
          <div className="absolute right-6 top-6 grid size-28 place-items-center rounded-full bg-[#ff765f] text-center text-xs font-semibold uppercase tracking-[0.1em] text-white shadow-xl">Baked<br />today</div>
        </div>
        <div className="flex flex-col p-6 sm:p-10 lg:p-14">
          <div className="my-auto py-20">
            <h2 className="text-[clamp(4.8rem,11vw,10rem)] font-semibold leading-[0.72] tracking-[-0.09em]">Fresh by <span className="font-serif font-normal italic text-[#ff765f]">seven.</span></h2>
            <p className="mt-8 max-w-sm text-base leading-7 text-[#5d2d26]/62">Small-batch bread, laminated pastry, and really good coffee. Until sold out.</p>
          </div>
          <a href="#sera-menu" className="flex items-center justify-between border-t border-[#5d2d26]/20 pt-5 text-sm font-semibold">Today&apos;s bake <ArrowRight className="size-4" /></a>
        </div>
      </section>

      <section id="sera-menu" className="border-y border-[#5d2d26]/18 bg-[#fff6ec] px-6 py-24 sm:px-10 lg:px-14 lg:py-32">
        <div className="grid gap-12 lg:grid-cols-[0.34fr_0.66fr]">
          <div>
            <p className="text-[10px] uppercase tracking-[0.16em] text-[#ff765f]">Today · while it lasts</p>
            <h3 className="mt-5 font-serif text-6xl italic tracking-[-0.05em] sm:text-7xl">The bake.</h3>
          </div>
          <div className="divide-y divide-[#5d2d26]/16 border-y border-[#5d2d26]/16">
            {[
              ["Country sourdough", "Stone-milled wheat · 900g", "$12"],
              ["Morning bun", "Brown sugar · orange · cardamom", "$6"],
              ["Olive loaf", "Castelvetrano olive · rosemary", "$14"],
              ["Seasonal danish", "Plum · almond cream", "$7"],
              ["Focaccia slice", "Tomato · sea salt · oregano", "$8"],
            ].map(([item, detail, price]) => (
              <div key={item} className="grid grid-cols-[1fr_auto] gap-4 py-5">
                <div><h4 className="text-lg font-semibold tracking-[-0.025em]">{item}</h4><p className="mt-1 text-xs text-[#5d2d26]/52">{detail}</p></div>
                <span className="font-mono text-sm">{price}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="sera-story" className="grid lg:grid-cols-2">
        <div className="bg-[#ff765f] p-7 text-[#fff6ec] sm:p-12 lg:p-16">
          <p className="text-[10px] uppercase tracking-[0.16em] text-white/68">Since 2019</p>
          <blockquote className="mt-16 font-serif text-4xl italic leading-[1.08] tracking-[-0.04em] sm:text-6xl">“Flour, water, salt, time. Nothing to hide behind.”</blockquote>
          <p className="mt-10 text-sm text-white/62">Mara Sera · Baker and owner</p>
        </div>
        <div className="flex flex-col justify-between p-7 sm:p-12 lg:p-16">
          <h3 className="text-5xl font-semibold leading-[0.92] tracking-[-0.065em] sm:text-7xl">Made slowly. Eaten immediately.</h3>
          <div className="mt-20 grid gap-5 border-t border-[#5d2d26]/18 pt-6 sm:grid-cols-2">
            <p className="text-sm leading-7 text-[#5d2d26]/62">Every loaf starts with our six-year starter and ferments overnight for flavor, texture, and a crust worth fighting over.</p>
            <p className="text-sm leading-7 text-[#5d2d26]/62">We work with regional grain, seasonal fruit, and producers whose names we know.</p>
          </div>
        </div>
      </section>

      <section id="sera-visit" className="border-t border-[#5d2d26]/18 bg-[#5d2d26] px-6 py-24 text-[#fff6ec] sm:px-10 lg:px-14 lg:py-28">
        <div className="grid gap-12 lg:grid-cols-[1fr_0.8fr] lg:items-end">
          <div>
            <p className="font-serif text-3xl italic text-[#ff9a86]">Come early.</p>
            <h3 className="mt-5 text-6xl font-semibold leading-[0.82] tracking-[-0.08em] sm:text-9xl">See you at seven.</h3>
          </div>
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="border-t border-white/20 pt-5"><MapPin className="size-5 text-[#ff765f]" /><p className="mt-5 text-sm leading-6 text-white/65">207 Pine Avenue<br />Long Beach, CA</p></div>
            <div className="border-t border-white/20 pt-5"><Clock3 className="size-5 text-[#ff765f]" /><p className="mt-5 text-sm leading-6 text-white/65">Tuesday—Sunday<br />7am—2pm</p></div>
          </div>
        </div>
      </section>

      <footer className="flex flex-col justify-between gap-4 bg-[#5d2d26] px-6 py-7 text-xs text-white/42 sm:flex-row sm:px-10 lg:px-14">
        <span className="font-serif text-xl italic text-white">Sera</span><Link href="/demos">All demos</Link><span>© 2026</span>
      </footer>
    </div>
  );
}

export function DemoShowcase() {
  const [activeIndex, setActiveIndex] = useState(0);
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const panelRef = useRef<HTMLDivElement>(null);

  const selectDemo = (index: number, returnToTop = false) => {
    setActiveIndex(index);
    if (returnToTop && panelRef.current) {
      window.scrollTo({ top: Math.max(panelRef.current.offsetTop - 136, 0), behavior: "smooth" });
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    let next = activeIndex;
    if (event.key === "ArrowRight") next = (activeIndex + 1) % demoTabs.length;
    else if (event.key === "ArrowLeft") next = (activeIndex - 1 + demoTabs.length) % demoTabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = demoTabs.length - 1;
    else return;
    event.preventDefault();
    selectDemo(next, true);
    tabRefs.current[next]?.focus();
  };

  return (
    <section className="bg-[#050505] text-white">
      <div className="sticky top-[68px] z-40 border-y border-white/12 bg-[#050505]/92 backdrop-blur-2xl">
        <div className="site-container flex min-h-20 flex-col gap-4 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-baseline gap-3">
            <h1 className="text-2xl font-semibold tracking-[-0.05em]">Demos</h1>
            <span className="text-[10px] uppercase tracking-[0.15em] text-white/32">Complete sites</span>
          </div>
          <div className="grid grid-cols-3 gap-1" role="tablist" aria-label="Choose a website demo">
            {demoTabs.map((demo, index) => (
              <button
                key={demo.id}
                ref={(element) => { tabRefs.current[index] = element; }}
                id={`demo-tab-${demo.id}`}
                type="button"
                role="tab"
                aria-selected={activeIndex === index}
                aria-controls="demo-panel"
                tabIndex={activeIndex === index ? 0 : -1}
                onClick={() => selectDemo(index, true)}
                onKeyDown={handleKeyDown}
                className={`min-w-0 border px-3 py-3 text-left transition-colors sm:min-w-40 sm:px-4 ${
                  activeIndex === index
                    ? "border-[#c9ff3b] bg-[#c9ff3b] text-[#050505]"
                    : "border-white/12 bg-white/4 text-white/52 hover:border-white/30 hover:text-white"
                }`}
              >
                <span className="block truncate text-xs font-semibold">{demo.name}</span>
                <span className={`mt-1 hidden text-[9px] uppercase tracking-[0.1em] sm:block ${activeIndex === index ? "text-black/50" : "text-white/28"}`}>{demo.type}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="site-container py-6 sm:py-10">
        <div
          ref={panelRef}
          id="demo-panel"
          role="tabpanel"
          aria-labelledby={`demo-tab-${demoTabs[activeIndex].id}`}
          tabIndex={0}
          className="demo-switch-in scroll-mt-36 overflow-hidden border border-white/12 shadow-[0_30px_120px_rgba(0,0,0,0.42)]"
          key={demoTabs[activeIndex].id}
        >
          {activeIndex === 0 ? <MossSite /> : activeIndex === 1 ? <NorthlineSite /> : <SeraSite />}
        </div>
      </div>
    </section>
  );
}
