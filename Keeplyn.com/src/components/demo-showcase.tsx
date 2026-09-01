"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowRight, ArrowUpRight, CalendarDays, Clock3, MapPin } from "lucide-react";
import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent, type MouseEvent as ReactMouseEvent } from "react";
import {
  DemoBookingPage,
  DemoContactPage,
  DemoPricingPage,
  MossHeader,
  NorthlineHeader,
  SeraHeader,
  type DemoSlug,
} from "@/components/demo-detail-pages";
import { DemoAboutPage, DemoFaqPage } from "@/components/demo-info-pages";
import { MossVines, SeraProofingField } from "@/components/demo-visual-systems";
import { NorthlineCareCore } from "@/components/northline-care-core";

const demoTabs = [
  { id: "moss", name: "Moss & Mortar", type: "Landscape studio" },
  { id: "northline", name: "Northline", type: "Family dentistry" },
  { id: "sera", name: "Sera", type: "Local bakery" },
] as const;

export type DemoPage = "home" | "about" | "faq" | "pricing" | "contact" | "booking";

const visualLayers = [0, 1, 2, 3, 4, 5, 6, 7, 8] as const;
const visualParticles = [0, 1, 2, 3, 4, 5] as const;

function visualStyle(index: number) {
  return { "--visual-index": index } as CSSProperties;
}

function MossKineticField() {
  return (
    <div className="moss-kinetic-field" aria-hidden="true">
      <div className="moss-kinetic-glow" />
      {visualLayers.map((index) => <span key={index} className="moss-contour" style={visualStyle(index)} />)}
      {visualParticles.map((index) => <span key={index} className="moss-seed" style={visualStyle(index)} />)}
      <div className="moss-axis"><span /><span /><span /><span /><span /></div>
    </div>
  );
}

function NorthlineKineticField() {
  return (
    <div className="northline-kinetic-field" aria-hidden="true">
      <div className="northline-dot-grid" />
      {visualLayers.slice(0, 5).map((index) => <span key={index} className="northline-orbit" style={visualStyle(index)} />)}
      {visualParticles.map((index) => <span key={index} className="northline-pulse" style={visualStyle(index)} />)}
      <div className="northline-smile"><span /><span /></div>
      <div className="northline-cross"><span /><span /></div>
    </div>
  );
}

function SeraKineticField() {
  return (
    <div className="sera-kinetic-field" aria-hidden="true">
      <div className="sera-sunburst" />
      <div className="sera-ferment-ring"><span>07</span></div>
      {visualParticles.map((index) => <span key={index} className="sera-bubble" style={visualStyle(index)} />)}
      <div className="sera-stripes" />
    </div>
  );
}

export function MossSite() {
  return (
    <div className="moss-world relative overflow-hidden bg-[#dfe5d6] text-[#203126]">
      <MossHeader active="home" />

      <section id="moss-top" className="moss-hero relative isolate grid min-h-[54rem] overflow-hidden bg-[#17261c] text-[#f3f5ed] shadow-[0_44px_100px_rgba(15,28,20,.28)] lg:grid-cols-[0.46fr_0.54fr]">
        <MossVines variant="hero" className="absolute inset-0 z-[6] size-full" />
        <div className="relative z-10 flex flex-col justify-between p-6 sm:p-10 lg:p-14">
          <div className="flex items-start justify-between gap-6">
            <p className="text-[10px] uppercase tracking-[0.18em] text-[#c9ff3b]">Landscape / California</p>
            <p className="text-right font-mono text-[10px] leading-5 tracking-[0.12em] text-white/58">38.57° N<br />121.47° W</p>
          </div>
          <div className="py-20 lg:py-0">
            <h2 className="text-[clamp(5rem,9vw,9rem)] font-semibold leading-[0.7] tracking-[-0.09em]">Wild,<span className="block font-serif font-normal italic text-[#c9ff3b]">with intent.</span></h2>
            <Link href="/demos/moss/about" className="group mt-12 flex w-fit items-center gap-4 border-b border-white/35 pb-3 text-sm font-semibold">Meet the studio <ArrowRight className="size-4 transition-transform group-hover:translate-x-2" aria-hidden="true" /></Link>
          </div>
          <p className="text-xs uppercase tracking-[0.16em] text-white/58">Land · light · water</p>
        </div>
        <div className="demo-film-grain relative min-h-[32rem] overflow-hidden border-t border-white/12 shadow-[-32px_0_90px_rgba(3,12,6,.34)] lg:min-h-0 lg:border-t-0 lg:border-l">
          <MossKineticField />
          <div className="absolute bottom-6 right-6 z-10 grid size-24 place-items-center rounded-full border border-[#c9ff3b]/55 text-center text-[10px] uppercase tracking-[0.14em] text-[#c9ff3b] sm:bottom-10 sm:right-10">Growing<br />system 01</div>
        </div>
      </section>

      <section id="moss-work" className="relative isolate px-5 py-20 sm:px-8 lg:px-12 lg:py-28">
        <MossVines variant="thread" className="absolute -right-[20%] top-[8%] z-[3] h-[86%] w-[78%] opacity-55" />
        <div className="relative z-10 flex items-end justify-between gap-8 pb-8">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#203126]/72">Selected ground · 24—26</p>
            <h3 className="mt-4 text-5xl font-semibold tracking-[-0.07em] sm:text-7xl">Three landscapes.</h3>
          </div>
          <span className="hidden font-serif text-4xl italic text-[#203126]/62 sm:block">One point of view.</span>
        </div>
        <div className="relative z-[4] grid auto-rows-[15rem] gap-4 sm:grid-cols-12 sm:auto-rows-[13rem] lg:auto-rows-[16rem]">
          <figure className="moss-depth-card group relative overflow-hidden rounded-[1.75rem] sm:col-span-8 sm:row-span-2">
            <Image src="/demos/moss-water-garden.png" alt="Native grasses surrounding a stone-lined water garden" fill sizes="(min-width: 640px) 66vw, 100vw" className="demo-gallery-image object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#101d14]/70 via-transparent to-transparent" />
            <figcaption className="absolute bottom-5 left-5 text-sm font-semibold text-white">South Slope <span className="ml-2 font-normal text-white/55">01</span></figcaption>
          </figure>
          <figure className="moss-depth-card group relative overflow-hidden rounded-[1.75rem] sm:col-span-4 sm:row-span-3">
            <Image src="/demos/moss-garden-passage.png" alt="Fern-lined stone garden passage" fill sizes="(min-width: 640px) 34vw, 100vw" className="demo-gallery-image object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#101d14]/72 via-transparent to-transparent" />
            <figcaption className="absolute bottom-5 left-5 text-sm font-semibold text-white">Night Passage <span className="ml-2 font-normal text-white/55">02</span></figcaption>
          </figure>
          <figure className="moss-depth-card group relative overflow-hidden rounded-[1.75rem] sm:col-span-5 sm:row-span-2">
            <Image src="/demos/moss-garden.jpg" alt="Lush courtyard garden illuminated at dusk" fill sizes="(min-width: 640px) 42vw, 100vw" className="demo-gallery-image object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#101d14]/72 via-transparent to-transparent" />
            <figcaption className="absolute bottom-5 left-5 text-sm font-semibold text-white">River House <span className="ml-2 font-normal text-white/55">03</span></figcaption>
          </figure>
          <div className="moss-depth-card relative flex overflow-hidden rounded-[1.75rem] bg-[#203126] p-6 text-[#edf1e9] sm:col-span-3 sm:row-span-2">
            <div className="absolute -right-12 -top-12 size-44 rounded-full border border-[#c9ff3b]/45" />
            <div className="absolute right-7 top-7 size-14 rounded-full bg-[#c9ff3b]" />
            <p className="mt-auto font-serif text-3xl italic leading-none">Land.<br />Light.<br />Water.</p>
          </div>
        </div>
      </section>

      <section id="moss-approach" className="relative isolate grid overflow-hidden bg-[#17261c] text-[#edf1e9] shadow-[0_42px_100px_rgba(15,28,20,.24)] lg:grid-cols-[0.64fr_0.36fr]">
        <MossVines variant="canopy" className="absolute inset-0 z-0 size-full opacity-45" />
        <div className="relative z-10 p-7 sm:p-12 lg:p-16">
          <p className="text-[10px] uppercase tracking-[0.18em] text-[#c9ff3b]">The method</p>
          <h3 className="mt-12 text-[clamp(4rem,8vw,8rem)] font-semibold leading-[0.78] tracking-[-0.08em]">Listen.<br />Shape.<br /><span className="font-serif font-normal italic text-[#c9ff3b]">Let grow.</span></h3>
        </div>
        <div className="relative z-[2] grid min-h-[28rem] grid-cols-2 grid-rows-2 shadow-[-30px_0_80px_rgba(4,14,8,.42)] lg:min-h-0">
          <div className="bg-[#6f806e]" />
          <div className="bg-[#d8decf]" />
          <div className="bg-[#9daa8b]" />
          <div className="relative overflow-hidden">
            <Image src="/demos/moss-garden-passage.png" alt="Deep green fern texture" fill sizes="(min-width: 1024px) 18vw, 50vw" className="object-cover transition-transform duration-1000 hover:scale-110" />
          </div>
        </div>
      </section>

      <section id="moss-contact" className="px-6 py-20 sm:px-10 lg:px-14 lg:py-28">
        <p className="text-[10px] uppercase tracking-[0.18em] text-[#203126]/45">Autumn 2026</p>
        <Link href="/demos/moss/contact" className="group mt-5 flex items-end justify-between border-y border-[#203126]/20 py-8">
          <span className="text-5xl font-semibold tracking-[-0.07em] sm:text-8xl">Grow with us.</span>
          <ArrowUpRight className="mb-2 size-9 transition-transform group-hover:-translate-y-2 group-hover:translate-x-2" aria-hidden="true" />
        </Link>
      </section>

      <footer className="flex flex-col justify-between gap-4 border-t border-[#203126]/20 px-6 py-7 text-xs text-[#203126]/72 sm:flex-row sm:px-10 lg:px-14">
        <span>Moss &amp; Mortar Landscape Studio</span><span>© 2026</span>
      </footer>
    </div>
  );
}

export function NorthlineSite() {
  return (
    <div className="northline-world bg-[#f3f7fb] text-[#173a5a]">
      <NorthlineHeader active="home" />

      <section id="northline-top" className="px-4 pb-5 sm:px-7 sm:pb-8">
        <div className="northline-depth-card grid min-h-[54rem] overflow-hidden rounded-[2.5rem] bg-[#dceef8] lg:grid-cols-[0.47fr_0.53fr]">
          <div className="relative z-10 flex flex-col justify-between p-7 sm:p-12 lg:p-14">
            <div className="flex items-center justify-between gap-4">
              <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#173a5a]/55">Oakland · CA</span>
              <span className="rounded-full border border-[#173a5a]/15 bg-white/45 px-4 py-2 text-[10px]">Accepting patients</span>
            </div>
            <div className="py-20 lg:py-0">
              <h2 className="text-[clamp(4.5rem,8vw,8rem)] font-semibold leading-[0.75] tracking-[-0.085em]">Care feels<br /><span className="text-[#c9483c]">different</span> here.</h2>
              <div className="mt-9 flex flex-wrap items-center gap-4"><Link href="/demos/northline/booking" className="rounded-full bg-[#ff725e] px-6 py-3 text-sm font-semibold text-white shadow-[0_16px_50px_rgba(255,114,94,.3)]">Book a first visit</Link><span className="text-xs text-[#173a5a]/45">40 minutes · no rush</span></div>
            </div>
            <p className="text-xs uppercase tracking-[0.16em] text-[#173a5a]/35">Talk · see · plan</p>
          </div>
          <div className="demo-film-grain northline-3d-stage relative min-h-[34rem] overflow-hidden border-t border-[#173a5a]/10 lg:min-h-0 lg:border-t-0 lg:border-l">
            <div className="absolute inset-0 opacity-65"><NorthlineKineticField /></div>
            <div className="absolute inset-0 z-[2]"><NorthlineCareCore /></div>
            <div className="absolute right-6 top-6 z-10 rounded-full border border-[#173a5a]/12 bg-white/60 px-4 py-2 text-[9px] font-semibold uppercase tracking-[0.14em] text-[#173a5a]/65 shadow-lg backdrop-blur-xl">Live 3D</div>
            <div className="absolute bottom-7 right-7 z-10 rounded-[1.5rem] bg-white/72 p-5 shadow-[0_24px_90px_rgba(23,58,90,.24)] backdrop-blur-xl sm:bottom-10 sm:right-10">
              <div className="flex items-center gap-3"><CalendarDays className="size-5 text-[#ff725e]" /><span className="text-xs font-semibold">Next opening</span></div>
              <p className="mt-3 text-3xl font-semibold tracking-[-0.055em]">Tue · 9:30</p>
            </div>
          </div>
        </div>
      </section>

      <section id="northline-services" className="px-5 py-20 sm:px-9 lg:py-28">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#ff725e]">Whole-person dentistry</p>
            <h3 className="mt-4 max-w-3xl text-5xl font-semibold leading-[0.9] tracking-[-0.07em] sm:text-7xl">Everything you need.<br />Nothing you don&apos;t.</h3>
          </div>
          <span className="text-sm text-[#173a5a]/45">01—03</span>
        </div>
        <div className="mt-12 grid gap-4 sm:grid-cols-3">
          {[
            ["01", "Everyday", "bg-[#d9edf8]"],
            ["02", "Restore", "bg-[#173a5a] text-white"],
            ["03", "Refine", "bg-[#ff725e] text-white"],
          ].map(([number, title, color], index) => (
            <article key={number} className={`northline-depth-card group relative min-h-[27rem] overflow-hidden rounded-[2rem] p-6 ${color}`}>
              <span className="relative z-10 text-xs font-semibold opacity-55">{number}</span>
              <div className="absolute inset-0 grid place-items-center">
                <div className={`demo-smile-arc demo-smile-arc-${index + 1}`} />
              </div>
              <h4 className="absolute bottom-6 left-6 text-3xl font-semibold tracking-[-0.055em]">{title}</h4>
            </article>
          ))}
        </div>
      </section>

      <section id="northline-visit" className="northline-depth-card mx-4 overflow-hidden rounded-[2.5rem] bg-[#173a5a] text-white sm:mx-7">
        <div className="grid lg:grid-cols-[0.58fr_0.42fr]">
          <div className="relative min-h-[34rem] overflow-hidden lg:min-h-[44rem]">
            <Image src="/demos/northline-clinic.jpg" alt="A relaxed conversation in the Northline clinic" fill sizes="(min-width: 1024px) 58vw, 100vw" className="demo-gallery-image object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#173a5a]/70 via-transparent to-transparent" />
            <p className="absolute bottom-7 left-7 text-sm font-semibold sm:bottom-10 sm:left-10">Real conversation. Clear choices.</p>
          </div>
          <div className="flex flex-col justify-between p-7 sm:p-12 lg:p-14">
            <div>
              <p className="text-[10px] uppercase tracking-[0.18em] text-[#ff9a89]">Your first visit</p>
              <h3 className="mt-6 text-5xl font-semibold leading-[0.88] tracking-[-0.07em] sm:text-7xl">Clear from<br />the start.</h3>
            </div>
            <ol className="mt-16 space-y-3">
              {["Talk", "See", "Plan"].map((title, index) => (
                <li key={title} className="flex items-center justify-between rounded-full border border-white/18 px-5 py-4">
                  <span className="text-sm font-semibold">{title}</span><span className="text-xs text-[#ff8f7d]">0{index + 1}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </section>

      <section id="northline-contact" className="px-6 py-24 sm:px-10 lg:px-14 lg:py-32">
        <div className="grid gap-10 lg:grid-cols-[0.62fr_0.38fr] lg:items-end">
          <div>
            <p className="text-[10px] uppercase tracking-[0.18em] text-[#ff725e]">Next opening</p>
            <h3 className="mt-5 text-5xl font-semibold leading-[0.9] tracking-[-0.07em] sm:text-8xl">Ready when you are.</h3>
          </div>
          <div className="northline-depth-card rounded-[1.5rem] border border-[#173a5a]/12 bg-white p-6">
            <div className="flex items-center gap-3 border-b border-[#173a5a]/12 pb-4"><CalendarDays className="size-5 text-[#ff725e]" /><span className="text-sm font-semibold">Next available</span></div>
            <p className="mt-7 text-4xl font-semibold tracking-[-0.06em]">Tuesday 14</p>
            <p className="mt-2 text-sm text-[#173a5a]/55">9:30am · New patient exam</p>
            <Link href="/demos/northline/booking" className="mt-8 flex items-center justify-between rounded-full bg-[#ff725e] px-5 py-3 text-sm font-semibold text-white">Request this time <ArrowRight className="size-4" /></Link>
          </div>
        </div>
      </section>

      <footer className="flex flex-col justify-between gap-5 bg-[#dcebf6] px-6 py-8 text-xs sm:flex-row sm:items-center sm:px-10 lg:px-14">
        <span className="text-base font-semibold">northline<span className="text-[#ff725e]">●</span></span><span>(510) 555-0144</span>
      </footer>
    </div>
  );
}

export function SeraSite() {
  return (
    <div className="sera-world bg-[#f6e8d8] text-[#5d2d26]">
      <SeraHeader active="home" />

      <section id="sera-top" className="sera-hero grid min-h-[54rem] overflow-hidden bg-[#f6e8d8] shadow-[0_42px_100px_rgba(93,45,38,.20)] lg:grid-cols-[0.54fr_0.46fr]">
        <div className="demo-film-grain relative min-h-[36rem] overflow-hidden bg-[#5d2d26] shadow-[32px_0_90px_rgba(93,45,38,.25)] lg:min-h-0">
          <SeraKineticField />
          <div className="absolute left-6 top-6 z-10 flex size-24 rotate-[-9deg] items-center justify-center rounded-full bg-[#ff765f] text-center text-[10px] font-bold uppercase tracking-[0.14em] text-white shadow-2xl sm:left-10 sm:top-10 sm:size-28">First light<br />First batch</div>
        </div>
        <div className="relative z-10 flex flex-col justify-between p-6 sm:p-10 lg:p-14">
          <p className="font-serif text-3xl italic text-[#b94a3d] sm:text-4xl">Doors at seven.</p>
          <div className="py-20 lg:py-0">
            <h2 className="text-[clamp(5rem,9vw,9rem)] font-semibold leading-[0.68] tracking-[-0.095em]">Come<br />hungry.</h2>
            <Link href="/demos/sera/about" className="group mt-10 flex w-fit items-center gap-4 border-b border-[#5d2d26]/35 pb-3 text-sm font-semibold">Meet the bakehouse <ArrowRight className="size-4 transition-transform group-hover:translate-x-2" aria-hidden="true" /></Link>
          </div>
          <p className="text-xs uppercase tracking-[0.16em] text-[#5d2d26]/68">Bread · pastry · coffee</p>
        </div>
      </section>

      <section id="sera-menu" className="bg-[#fff6ec] px-5 py-20 sm:px-9 lg:py-28">
        <div className="flex items-end justify-between gap-8">
          <div><p className="text-[10px] uppercase tracking-[0.18em] text-[#ff765f]">Today · while it lasts</p><h3 className="mt-4 font-serif text-6xl italic tracking-[-0.06em] sm:text-8xl">The bake.</h3></div>
          <span className="hidden text-sm text-[#5d2d26]/42 sm:block">Tuesday / 01 September</span>
        </div>
        <div className="mt-10 grid gap-3 lg:grid-cols-12 lg:grid-rows-[18rem_18rem]">
          <figure className="sera-depth-card group relative min-h-[32rem] overflow-hidden lg:col-span-5 lg:row-span-2 lg:min-h-0">
            <Image src="/demos/sera-bread.jpg" alt="A bakery counter filled with artisan sourdough" fill sizes="(min-width: 1024px) 42vw, 100vw" className="demo-gallery-image object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#4b201a]/82 via-transparent to-transparent" />
            <figcaption className="absolute bottom-6 left-6 text-[#fff6ec]"><span className="font-serif text-4xl italic">Country</span><span className="ml-3 font-mono text-sm text-white/65">$12</span></figcaption>
          </figure>
          <div className="sera-depth-card relative flex min-h-[18rem] overflow-hidden bg-[#ff765f] p-6 text-[#fff6ec] lg:col-span-4">
            <div className="absolute -right-8 -top-8 size-48 rotate-12 rounded-[2.5rem] border-[18px] border-[#ffb09e]/55 transition-transform duration-700 hover:rotate-45" />
            <p className="mt-auto font-serif text-4xl italic">Morning bun <span className="font-mono text-sm not-italic text-white/68">$6</span></p>
          </div>
          <div className="sera-depth-card relative flex min-h-[18rem] overflow-hidden bg-[#5d2d26] p-6 text-[#fff6ec] lg:col-span-3">
            <div className="absolute right-6 top-6 size-28 rounded-full bg-[#f4c96f] shadow-[0_0_0_20px_rgba(244,201,111,.14)]" />
            <p className="mt-auto font-serif text-4xl italic">Danish <span className="font-mono text-sm not-italic text-white/60">$7</span></p>
          </div>
          <div className="sera-depth-card relative flex min-h-[18rem] overflow-hidden bg-[#f4c96f] p-6 lg:col-span-7">
            <div className="sera-menu-wave" aria-hidden="true" />
            <p className="relative z-10 mt-auto font-serif text-4xl italic">Olive loaf <span className="font-mono text-sm not-italic text-[#5d2d26]/58">$14</span></p>
          </div>
        </div>
      </section>

      <section id="sera-story" className="relative isolate grid overflow-hidden bg-[#ff765f] text-[#fff6ec] shadow-[0_34px_90px_rgba(93,45,38,.22)] lg:grid-cols-[0.32fr_0.68fr]">
        <SeraProofingField className="absolute -right-[18%] -top-[60%] z-0 h-[220%] w-[76%] opacity-30" />
        <div className="flex min-h-[18rem] items-center justify-center border-b border-white/20 p-7 lg:min-h-0 lg:border-r lg:border-b-0">
          <div className="grid size-40 place-items-center rounded-full border border-white/35 text-center font-mono text-xs leading-5">FERMENTED<br />18 HOURS</div>
        </div>
        <div className="relative z-10 p-7 sm:p-12 lg:p-16">
          <blockquote className="max-w-5xl font-serif text-5xl italic leading-[0.98] tracking-[-0.05em] sm:text-7xl">“Flour, water, salt, time.”</blockquote>
        </div>
      </section>

      <section id="sera-visit" className="relative border-t border-[#5d2d26]/18 bg-[#5d2d26] px-6 py-24 text-[#fff6ec] sm:px-10 lg:px-14 lg:py-28">
        <div className="grid gap-12 lg:grid-cols-[1fr_0.8fr] lg:items-end">
          <div>
            <p className="font-serif text-3xl italic text-[#ff9a86]">Come early.</p>
            <h3 className="mt-5 text-6xl font-semibold leading-[0.82] tracking-[-0.08em] sm:text-9xl">Seven sharp.</h3>
          </div>
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="border-t border-white/20 pt-5"><MapPin className="size-5 text-[#ff765f]" /><p className="mt-5 text-sm leading-6 text-white/65">207 Pine Avenue<br />Long Beach, CA</p></div>
            <div className="border-t border-white/20 pt-5"><Clock3 className="size-5 text-[#ff765f]" /><p className="mt-5 text-sm leading-6 text-white/65">Tuesday—Sunday<br />7am—2pm</p></div>
          </div>
        </div>
      </section>

      <footer className="flex flex-col justify-between gap-4 bg-[#5d2d26] px-6 py-7 text-xs text-white/42 sm:flex-row sm:px-10 lg:px-14">
        <span className="font-serif text-xl italic text-white">Sera</span><span>© 2026</span>
      </footer>
    </div>
  );
}

type DemoShowcaseProps = {
  initialDemo?: DemoSlug;
  initialPage?: DemoPage;
};

export function DemoShowcase({ initialDemo = "moss", initialPage = "home" }: DemoShowcaseProps) {
  const initialIndex = Math.max(demoTabs.findIndex((demo) => demo.id === initialDemo), 0);
  const [activeIndex, setActiveIndex] = useState(initialIndex);
  const [activePage, setActivePage] = useState<DemoPage>(initialPage);
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const selectorBarRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [activeIndex, activePage]);

  const showDemoPage = (index: number, page: DemoPage, returnToTop = true) => {
    setActiveIndex(index);
    setActivePage(page);
    const demo = demoTabs[index];
    window.history.replaceState(null, "", `/demos?demo=${demo.id}&page=${page}`);
    if (returnToTop) {
      window.scrollTo({ top: 0, behavior: "auto" });
      window.requestAnimationFrame(() => {
        window.scrollTo({ top: 0, behavior: "auto" });
      });
    }
  };

  const selectDemo = (index: number) => {
    showDemoPage(index, "home", true);
  };

  const handleDemoNavigation = (event: ReactMouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    const link = target.closest("a");
    if (!link) return;

    const href = link.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("mailto:")) return;

    if (href === "/demos") {
      event.preventDefault();
      showDemoPage(activeIndex, "home", true);
      return;
    }

    const match = href.match(/^\/demos\/(moss|northline|sera)(?:\/(about|faq|pricing|contact|booking))?$/);
    if (!match) return;

    event.preventDefault();
    const nextIndex = demoTabs.findIndex((demo) => demo.id === match[1]);
    if (nextIndex < 0) return;
    showDemoPage(nextIndex, (match[2] as DemoPage | undefined) ?? "home", true);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    let next = activeIndex;
    if (event.key === "ArrowRight") next = (activeIndex + 1) % demoTabs.length;
    else if (event.key === "ArrowLeft") next = (activeIndex - 1 + demoTabs.length) % demoTabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = demoTabs.length - 1;
    else return;
    event.preventDefault();
    selectDemo(next);
    tabRefs.current[next]?.focus();
  };

  return (
    <section className="bg-[#050505] text-white">
      <div ref={selectorBarRef} className="sticky top-[68px] z-40 border-y border-white/12 bg-[#050505]/92 backdrop-blur-2xl">
        <div className="site-container grid min-h-20 items-center gap-4 py-4 lg:grid-cols-[1fr_30rem]">
          <h1 className="text-7xl font-semibold leading-none tracking-[-0.07em]">Demos</h1>
          <div className="grid w-full grid-cols-3 gap-1" role="tablist" aria-label="Choose a website demo">
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
                onClick={() => selectDemo(index)}
                onKeyDown={handleKeyDown}
                className={`flex min-h-14 min-w-0 flex-col justify-center border px-3 py-3 text-left transition-colors sm:px-4 ${
                  activeIndex === index
                    ? "border-[#c9ff3b] bg-[#c9ff3b] text-[#050505]"
                    : "border-white/12 bg-white/4 text-white/52 hover:border-white/30 hover:text-white"
                }`}
              >
                <span className="block truncate text-xs font-semibold">{demo.name}</span>
                <span className={`mt-1 hidden text-[9px] uppercase tracking-[0.1em] sm:block ${activeIndex === index ? "text-black/72" : "text-white/58"}`}>{demo.type}</span>
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
          onClickCapture={handleDemoNavigation}
          className="demo-switch-in scroll-mt-36 overflow-hidden border border-white/12 shadow-[0_30px_120px_rgba(0,0,0,0.42)]"
          key={`${demoTabs[activeIndex].id}-${activePage}`}
        >
          {activePage === "about" ? (
            <DemoAboutPage demo={demoTabs[activeIndex].id} />
          ) : activePage === "faq" ? (
            <DemoFaqPage demo={demoTabs[activeIndex].id} />
          ) : activePage === "pricing" ? (
            <DemoPricingPage demo={demoTabs[activeIndex].id} />
          ) : activePage === "contact" ? (
            <DemoContactPage demo={demoTabs[activeIndex].id} />
          ) : activePage === "booking" ? (
            <DemoBookingPage demo={demoTabs[activeIndex].id} />
          ) : activeIndex === 0 ? (
            <MossSite />
          ) : activeIndex === 1 ? (
            <NorthlineSite />
          ) : (
            <SeraSite />
          )}
        </div>
      </div>
    </section>
  );
}
