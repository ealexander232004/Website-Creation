"use client";

import Image from "next/image";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  CalendarDays,
  Clock3,
  MapPin,
  Move3D,
} from "lucide-react";
import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type MouseEvent as ReactMouseEvent,
} from "react";
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
import { DemoWorld } from "@/components/demo-world-slot";
import { MossVines, SeraProofingField } from "@/components/demo-visual-systems";

const demoTabs = [
  { id: "moss", name: "Moss & Mortar", type: "Landscape studio", accent: "#c9ff3b", ink: "#102018" },
  { id: "northline", name: "Northline", type: "Family dentistry", accent: "#ff725e", ink: "#ffffff" },
  { id: "sera", name: "Sera", type: "Neighborhood bakery", accent: "#f4c96f", ink: "#5d2d26" },
] as const;

const northlineServices = ["Preventive", "Restorative", "Cosmetic", "Family"] as const;

const seraMenu = [
  ["Country sourdough", "$12"],
  ["Morning bun", "$6"],
  ["Seasonal danish", "$7"],
  ["Olive loaf", "$14"],
] as const;

export type DemoPage = "home" | "about" | "faq" | "pricing" | "contact" | "booking";

export function MossSite() {
  return (
    <div className="moss-world overflow-hidden bg-[#dfe5d6] text-[#203126]">
      <MossHeader active="home" />

      <section className="grid min-h-[49rem] bg-[#132219] text-[#f3f5ed] lg:grid-cols-[0.43fr_0.57fr]">
        <div className="relative z-10 flex flex-col justify-between border-b border-white/10 p-7 sm:p-11 lg:border-r lg:border-b-0 lg:p-14">
          <div className="flex items-start justify-between gap-8">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9ff3b]">Landscape / California</p>
            <p className="text-right font-mono text-[9px] leading-5 tracking-[0.14em] text-white/40">38.57° N<br />121.47° W</p>
          </div>

          <div className="py-20 lg:py-10">
            <h2 className="max-w-[8ch] text-[clamp(4.7rem,8.4vw,8.6rem)] font-semibold leading-[0.74] tracking-[-0.09em]">
              Wild,
              <span className="block font-serif font-normal italic text-[#c9ff3b]">with intent.</span>
            </h2>
            <div className="mt-11 flex flex-wrap items-center gap-6">
              <Link href="/demos/moss/booking" className="group inline-flex items-center gap-4 rounded-full bg-[#c9ff3b] px-6 py-3 text-sm font-semibold text-[#132219] shadow-[0_20px_55px_rgba(201,255,59,.18)]">
                Start a garden <ArrowRight className="size-4 transition-transform group-hover:translate-x-1.5" aria-hidden="true" />
              </Link>
              <span className="text-[10px] uppercase tracking-[0.16em] text-white/42">Autumn 2026</span>
            </div>
          </div>

          <p className="max-w-xs text-xs leading-6 text-white/48">Gardens composed as living terrain—rooted in season, shade, and the life around them.</p>
        </div>

        <div className="moss-world-stage demo-world-stage relative min-h-[35rem] overflow-hidden lg:min-h-0">
          <MossVines variant="canopy" className="absolute inset-0 z-0 size-full opacity-30" />
          <DemoWorld variant="moss" className="relative z-[2] size-full" />
          <div className="demo-stage-label left-6 top-6 sm:left-9 sm:top-9"><Move3D className="size-3.5" aria-hidden="true" /> Living terrain</div>
          <div className="absolute bottom-7 right-7 z-10 grid size-24 place-items-center rounded-full border border-[#c9ff3b]/36 bg-[#132219]/34 text-center font-mono text-[9px] uppercase leading-4 tracking-[0.15em] text-[#c9ff3b] backdrop-blur-md sm:bottom-10 sm:right-10">Drag the<br />canopy</div>
        </div>
      </section>

      <section className="px-5 py-20 sm:px-9 lg:px-12 lg:py-28">
        <div className="mx-auto max-w-[92rem]">
          <div className="flex flex-col justify-between gap-5 border-b border-[#203126]/18 pb-8 sm:flex-row sm:items-end">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#203126]/48">Selected ground · 24—26</p>
              <h3 className="mt-4 text-5xl font-semibold tracking-[-0.07em] sm:text-7xl">Land, edited lightly.</h3>
            </div>
            <Link href="/demos/moss/about" className="group inline-flex items-center gap-3 text-sm font-semibold">The studio <ArrowUpRight className="size-4 transition-transform group-hover:-translate-y-1 group-hover:translate-x-1" aria-hidden="true" /></Link>
          </div>

          <div className="mt-5 grid gap-5 lg:grid-cols-12 lg:grid-rows-[17rem_17rem]">
            <figure className="moss-depth-card group relative min-h-[32rem] overflow-hidden rounded-[2.25rem] lg:col-span-7 lg:row-span-2 lg:min-h-0">
              <Image src="/demos/moss-water-garden.png" alt="Native grasses surrounding a stone-lined water garden" fill sizes="(min-width: 1024px) 58vw, 100vw" className="demo-gallery-image object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0d1b12]/76 via-transparent to-transparent" />
              <figcaption className="absolute inset-x-7 bottom-7 flex items-end justify-between gap-5 text-white">
                <span className="text-2xl font-semibold tracking-[-0.04em]">South Slope</span>
                <span className="font-mono text-[9px] uppercase tracking-[0.15em] text-white/55">Water / native grass</span>
              </figcaption>
            </figure>

            <aside className="moss-field-ledger relative overflow-hidden rounded-[2.25rem] border border-[#203126]/16 bg-[#edf1e9] p-7 lg:col-span-5">
              <MossVines variant="thread" className="absolute -right-20 -top-24 h-[25rem] w-[34rem] opacity-34" />
              <div className="relative z-10 flex h-full flex-col justify-between">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#203126]/42">Field ledger</p>
                <div className="grid grid-cols-2 gap-x-5 gap-y-7">
                  <div><strong className="text-4xl tracking-[-0.06em]">86%</strong><p className="mt-1 text-xs text-[#203126]/52">native planting</p></div>
                  <div><strong className="text-4xl tracking-[-0.06em]">−42%</strong><p className="mt-1 text-xs text-[#203126]/52">summer water</p></div>
                  <div><strong className="text-4xl tracking-[-0.06em]">4</strong><p className="mt-1 text-xs text-[#203126]/52">seasonal layers</p></div>
                  <div><strong className="text-4xl tracking-[-0.06em]">1</strong><p className="mt-1 text-xs text-[#203126]/52">living system</p></div>
                </div>
              </div>
            </aside>

            <figure className="moss-depth-card group relative min-h-[23rem] overflow-hidden rounded-[2.25rem] lg:col-span-5 lg:min-h-0">
              <Image src="/demos/moss-garden-passage.png" alt="Fern-lined stone garden passage" fill sizes="(min-width: 1024px) 42vw, 100vw" className="demo-gallery-image object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0d1b12]/74 via-transparent to-transparent" />
              <figcaption className="absolute bottom-6 left-6 text-xl font-semibold text-white">Night Passage</figcaption>
            </figure>
          </div>
        </div>
      </section>

      <section className="px-5 pb-20 sm:px-9 lg:px-12 lg:pb-28">
        <div className="moss-system-panel mx-auto grid max-w-[92rem] overflow-hidden rounded-[2.5rem] bg-[#1c3022] text-[#edf1e9] shadow-[0_40px_110px_rgba(16,35,22,.25)] lg:grid-cols-[0.52fr_0.48fr]">
          <div className="relative min-h-[31rem] overflow-hidden">
            <Image src="/demos/moss-garden.jpg" alt="Lush courtyard garden illuminated at dusk" fill sizes="(min-width: 1024px) 52vw, 100vw" className="object-cover" />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-[#1c3022]/45" />
          </div>
          <div className="flex flex-col justify-between p-8 sm:p-12 lg:p-14">
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-[#c9ff3b]">A garden is never finished</p>
              <h3 className="mt-7 text-5xl font-semibold leading-[0.9] tracking-[-0.07em] sm:text-7xl">Designed for the next season.</h3>
            </div>
            <div className="mt-16 flex items-end justify-between gap-8 border-t border-white/16 pt-6">
              <p className="max-w-xs text-sm leading-7 text-white/52">Structure now. Change over time. Beauty in both.</p>
              <Link href="/demos/moss/faq" aria-label="Read Moss and Mortar frequently asked questions" className="grid size-12 shrink-0 place-items-center rounded-full border border-[#c9ff3b]/45 text-[#c9ff3b]"><ArrowUpRight className="size-5" aria-hidden="true" /></Link>
            </div>
          </div>
        </div>
      </section>

      <section className="px-6 py-20 sm:px-10 lg:px-14 lg:py-28">
        <Link href="/demos/moss/contact" className="group mx-auto flex max-w-[92rem] items-end justify-between gap-8 border-y border-[#203126]/20 py-9">
          <span className="text-5xl font-semibold tracking-[-0.07em] sm:text-8xl">Grow with us.</span>
          <ArrowUpRight className="mb-2 size-9 shrink-0 transition-transform group-hover:-translate-y-2 group-hover:translate-x-2" aria-hidden="true" />
        </Link>
      </section>

      <footer className="flex flex-col justify-between gap-4 border-t border-[#203126]/20 px-6 py-7 text-xs text-[#203126]/58 sm:flex-row sm:px-10 lg:px-14"><span>Moss &amp; Mortar Landscape Studio</span><span>© 2026</span></footer>
    </div>
  );
}

export function NorthlineSite() {
  return (
    <div className="northline-world overflow-hidden bg-[#f3f7fb] text-[#173a5a]">
      <NorthlineHeader active="home" />

      <section className="px-4 pb-5 sm:px-7 sm:pb-8">
        <div className="northline-hero-shell grid min-h-[49rem] overflow-hidden rounded-[2.75rem] bg-[#dceef8] shadow-[0_38px_110px_rgba(23,58,90,.15)] lg:grid-cols-[0.44fr_0.56fr]">
          <div className="relative z-10 flex flex-col justify-between p-8 sm:p-12 lg:p-14">
            <div className="flex items-center justify-between gap-5">
              <span className="text-[10px] font-semibold uppercase tracking-[0.19em] text-[#173a5a]/48">Oakland · CA</span>
              <span className="rounded-full border border-[#173a5a]/12 bg-white/58 px-4 py-2 text-[10px] font-semibold shadow-sm">Accepting patients</span>
            </div>

            <div className="py-20 lg:py-8">
              <h2 className="text-[clamp(4.3rem,7.8vw,8rem)] font-semibold leading-[0.78] tracking-[-0.085em]">Care feels<br /><span className="text-[#c9483c]">different</span> here.</h2>
              <div className="mt-10 flex flex-wrap items-center gap-5">
                <Link href="/demos/northline/booking" className="group inline-flex items-center gap-3 rounded-full bg-[#ff725e] px-6 py-3 text-sm font-semibold text-white shadow-[0_18px_50px_rgba(255,114,94,.28)]">Book a first visit <ArrowRight className="size-4 transition-transform group-hover:translate-x-1.5" aria-hidden="true" /></Link>
                <span className="text-xs text-[#173a5a]/45">90 minutes · no rush</span>
              </div>
            </div>

            <p className="max-w-xs text-xs leading-6 text-[#173a5a]/48">Comfort-forward dentistry, explained clearly and paced around you.</p>
          </div>

          <div className="northline-world-stage demo-world-stage relative min-h-[35rem] overflow-hidden border-t border-[#173a5a]/10 lg:min-h-0 lg:border-t-0 lg:border-l">
            <div className="northline-stage-grid absolute inset-0" aria-hidden="true" />
            <DemoWorld variant="northline" className="relative z-[2] size-full" />
            <div className="demo-stage-label right-6 top-6 sm:right-9 sm:top-9"><Move3D className="size-3.5" aria-hidden="true" /> Responsive care object</div>
            <div className="absolute bottom-7 left-7 z-10 rounded-[1.35rem] border border-white/62 bg-white/72 p-5 shadow-[0_24px_75px_rgba(23,58,90,.18)] backdrop-blur-xl sm:bottom-10 sm:left-10">
              <div className="flex items-center gap-3"><CalendarDays className="size-4 text-[#ff725e]" aria-hidden="true" /><span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#173a5a]/56">Next opening</span></div>
              <p className="mt-2 text-2xl font-semibold tracking-[-0.05em]">Tue · 9:30</p>
            </div>
          </div>
        </div>
      </section>

      <section className="px-5 py-20 sm:px-9 lg:py-28">
        <div className="mx-auto max-w-[92rem]">
          <div className="grid gap-8 lg:grid-cols-[0.64fr_0.36fr] lg:items-end">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9483c]">Whole-person dentistry</p>
              <h3 className="mt-5 max-w-5xl text-5xl font-semibold leading-[0.9] tracking-[-0.07em] sm:text-7xl">Clinical precision.<br />Human temperature.</h3>
            </div>
            <div className="flex flex-wrap gap-2 lg:justify-end">
              {northlineServices.map((service) => <span key={service} className="rounded-full border border-[#173a5a]/14 bg-white px-4 py-2 text-xs font-semibold shadow-[0_8px_25px_rgba(23,58,90,.06)]">{service}</span>)}
            </div>
          </div>

          <div className="mt-12 grid gap-5 lg:grid-cols-12 lg:grid-rows-[18rem_18rem]">
            <figure className="northline-depth-card group relative min-h-[35rem] overflow-hidden rounded-[2.5rem] lg:col-span-7 lg:row-span-2 lg:min-h-0">
              <Image src="/demos/northline-clinic.jpg" alt="A relaxed conversation in the Northline clinic" fill sizes="(min-width: 1024px) 58vw, 100vw" className="demo-gallery-image object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#102f4a]/72 via-transparent to-transparent" />
              <figcaption className="absolute inset-x-8 bottom-8 flex items-end justify-between gap-6 text-white"><span className="max-w-md text-3xl font-semibold leading-tight tracking-[-0.04em]">The appointment starts with a conversation.</span><span className="hidden rounded-full border border-white/28 px-4 py-2 text-[10px] uppercase tracking-[0.14em] sm:block">No rush</span></figcaption>
            </figure>

            <article className="northline-depth-card relative overflow-hidden rounded-[2.5rem] bg-[#173a5a] p-8 text-white lg:col-span-5">
              <div className="northline-soft-orbit absolute -right-20 -top-20" aria-hidden="true" />
              <div className="relative z-10 flex h-full flex-col justify-between"><span className="text-[10px] uppercase tracking-[0.16em] text-[#ff9a89]">Time changes care</span><strong className="text-[5.5rem] leading-none tracking-[-0.09em] sm:text-[7rem]">90</strong><p className="text-sm text-white/52">unhurried minutes for a first visit</p></div>
            </article>

            <article className="northline-depth-card relative overflow-hidden rounded-[2.5rem] border border-[#173a5a]/10 bg-white p-8 lg:col-span-5">
              <div className="flex h-full flex-col justify-between"><span className="text-[10px] uppercase tracking-[0.16em] text-[#c9483c]">A clear plan</span><p className="max-w-md text-3xl font-semibold leading-tight tracking-[-0.05em]">See what we see. Know what it costs. Choose without pressure.</p><Link href="/demos/northline/faq" className="group inline-flex w-fit items-center gap-3 text-sm font-semibold">Questions, answered <ArrowRight className="size-4 transition-transform group-hover:translate-x-1.5" aria-hidden="true" /></Link></div>
            </article>
          </div>
        </div>
      </section>

      <section className="px-4 pb-20 sm:px-7 lg:pb-28">
        <div className="northline-depth-card mx-auto grid max-w-[92rem] overflow-hidden rounded-[2.75rem] bg-[#ff725e] text-white lg:grid-cols-[0.62fr_0.38fr]">
          <div className="p-8 sm:p-12 lg:p-16">
            <p className="text-[10px] uppercase tracking-[0.19em] text-white/62">Dentistry without the edge</p>
            <h3 className="mt-7 max-w-4xl text-5xl font-semibold leading-[0.9] tracking-[-0.07em] sm:text-8xl">Ready when you are.</h3>
          </div>
          <div className="flex flex-col justify-between border-t border-white/22 bg-[#173a5a] p-8 sm:p-12 lg:border-t-0 lg:border-l">
            <div><CalendarDays className="size-5 text-[#ff8f7d]" aria-hidden="true" /><p className="mt-7 text-4xl font-semibold tracking-[-0.06em]">Tuesday 14</p><p className="mt-2 text-sm text-white/52">9:30am · New patient exam</p></div>
            <Link href="/demos/northline/booking" className="group mt-12 flex items-center justify-between rounded-full bg-white px-5 py-3 text-sm font-semibold text-[#173a5a]">Request this time <ArrowRight className="size-4 transition-transform group-hover:translate-x-1.5" aria-hidden="true" /></Link>
          </div>
        </div>
      </section>

      <footer className="flex flex-col justify-between gap-5 bg-[#dcebf6] px-6 py-8 text-xs sm:flex-row sm:items-center sm:px-10 lg:px-14"><span className="text-base font-semibold">northline<span className="text-[#ff725e]">●</span></span><span>(510) 555-0144</span></footer>
    </div>
  );
}

export function SeraSite() {
  return (
    <div className="sera-world overflow-hidden bg-[#f6e8d8] text-[#5d2d26]">
      <SeraHeader active="home" />

      <section className="grid min-h-[49rem] bg-[#f6e8d8] shadow-[0_40px_110px_rgba(93,45,38,.16)] lg:grid-cols-[0.57fr_0.43fr]">
        <div className="sera-world-stage demo-world-stage relative min-h-[36rem] overflow-hidden bg-[#5d2d26] lg:min-h-0">
          <SeraProofingField className="absolute -left-1/4 -top-1/4 z-0 h-[150%] w-[150%] opacity-12" />
          <DemoWorld variant="sera" className="relative z-[2] size-full" />
          <div className="demo-stage-label left-6 top-6 border-white/20 bg-[#5d2d26]/45 text-[#fff6ec] sm:left-9 sm:top-9"><Move3D className="size-3.5" aria-hidden="true" /> Proofing in real time</div>
          <div className="absolute bottom-7 right-7 z-10 rounded-full bg-[#ff765f] px-5 py-3 font-serif text-lg italic text-white shadow-[0_20px_60px_rgba(93,45,38,.32)] sm:bottom-10 sm:right-10">First batch · 7:00</div>
        </div>

        <div className="relative z-10 flex flex-col justify-between border-t border-[#5d2d26]/12 p-7 sm:p-11 lg:border-t-0 lg:border-l lg:p-14">
          <p className="font-serif text-3xl italic text-[#b94a3d] sm:text-4xl">Doors at seven.</p>
          <div className="py-20 lg:py-8">
            <h2 className="text-[clamp(5rem,8.8vw,9rem)] font-semibold leading-[0.68] tracking-[-0.095em]">Come<br />hungry.</h2>
            <div className="mt-11 flex flex-wrap items-center gap-6">
              <Link href="/demos/sera/about" className="group inline-flex items-center gap-4 rounded-full bg-[#5d2d26] px-6 py-3 text-sm font-semibold text-[#fff6ec] shadow-[0_20px_55px_rgba(93,45,38,.16)]">Meet the bakehouse <ArrowRight className="size-4 transition-transform group-hover:translate-x-1.5" aria-hidden="true" /></Link>
              <span className="text-[10px] uppercase tracking-[0.16em] text-[#5d2d26]/48">Bread · pastry · coffee</span>
            </div>
          </div>
          <p className="max-w-xs text-xs leading-6 text-[#5d2d26]/52">Long-fermented bread and morning pastry, made for the neighborhood.</p>
        </div>
      </section>

      <section className="bg-[#fff6ec] px-5 py-20 sm:px-9 lg:px-12 lg:py-28">
        <div className="mx-auto max-w-[92rem]">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#ff765f]">Today · while it lasts</p><h3 className="mt-4 font-serif text-6xl italic tracking-[-0.06em] sm:text-8xl">The bake.</h3></div><span className="text-xs text-[#5d2d26]/42">Tuesday / 01 September</span></div>

          <div className="mt-12 grid gap-5 lg:grid-cols-12">
            <figure className="sera-depth-card group relative min-h-[38rem] overflow-hidden rounded-[2.5rem] lg:col-span-7">
              <Image src="/demos/sera-bread.jpg" alt="A bakery counter filled with artisan sourdough" fill sizes="(min-width: 1024px) 58vw, 100vw" className="demo-gallery-image object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#4a1d18]/80 via-transparent to-transparent" />
              <figcaption className="absolute inset-x-8 bottom-8 flex items-end justify-between gap-6 text-[#fff6ec]"><span className="font-serif text-5xl italic tracking-[-0.04em]">Country</span><span className="font-mono text-sm text-white/65">$12</span></figcaption>
            </figure>

            <div className="sera-menu-board sera-depth-card relative overflow-hidden rounded-[2.5rem] border border-[#5d2d26]/14 bg-[#f6e8d8] p-8 lg:col-span-5 lg:p-10">
              <div className="sera-menu-orbit" aria-hidden="true" />
              <div className="relative z-10 flex h-full min-h-[34rem] flex-col">
                <p className="font-serif text-3xl italic text-[#ff765f]">On the counter</p>
                <div className="mt-auto">
                  {seraMenu.map(([item, price]) => (
                    <div key={item} className="flex items-center justify-between gap-5 border-t border-[#5d2d26]/16 py-5">
                      <span className="text-lg font-semibold tracking-[-0.035em]">{item}</span>
                      <span className="font-mono text-xs text-[#5d2d26]/52">{price}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="relative isolate overflow-hidden bg-[#ff765f] px-7 py-20 text-[#fff6ec] sm:px-12 lg:px-16 lg:py-28">
        <SeraProofingField className="absolute -right-[16%] -top-[110%] z-0 h-[320%] w-[72%] opacity-16" />
        <div className="relative z-10 mx-auto grid max-w-[92rem] gap-12 lg:grid-cols-[0.3fr_0.7fr] lg:items-center">
          <div className="grid size-44 place-items-center rounded-full border border-white/35 text-center font-mono text-[10px] uppercase leading-5 tracking-[0.16em] shadow-[inset_0_0_0_16px_rgba(255,255,255,.05)]">Fermented<br />18 hours</div>
          <blockquote className="max-w-5xl font-serif text-5xl italic leading-[0.98] tracking-[-0.05em] sm:text-8xl">“Flour, water, salt, time.”</blockquote>
        </div>
      </section>

      <section className="bg-[#5d2d26] px-6 py-24 text-[#fff6ec] sm:px-10 lg:px-14 lg:py-28">
        <div className="mx-auto grid max-w-[92rem] gap-12 lg:grid-cols-[1fr_0.8fr] lg:items-end">
          <div><p className="font-serif text-3xl italic text-[#ff9a86]">Come early.</p><h3 className="mt-5 text-6xl font-semibold leading-[0.82] tracking-[-0.08em] sm:text-9xl">Seven sharp.</h3></div>
          <div className="grid gap-6 sm:grid-cols-2">
            <div className="rounded-[1.75rem] border border-white/14 bg-white/5 p-6"><MapPin className="size-5 text-[#ff765f]" aria-hidden="true" /><p className="mt-7 text-sm leading-6 text-white/62">207 Pine Avenue<br />Long Beach, CA</p></div>
            <div className="rounded-[1.75rem] border border-white/14 bg-white/5 p-6"><Clock3 className="size-5 text-[#ff765f]" aria-hidden="true" /><p className="mt-7 text-sm leading-6 text-white/62">Tuesday—Sunday<br />7am—2pm</p></div>
          </div>
        </div>
      </section>

      <footer className="flex flex-col justify-between gap-4 bg-[#5d2d26] px-6 py-7 text-xs text-white/42 sm:flex-row sm:px-10 lg:px-14"><span className="font-serif text-xl italic text-white">Sera</span><span>© 2026</span></footer>
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
  const activeDemo = demoTabs[activeIndex];
  const selectorStyle = {
    "--demo-accent": activeDemo.accent,
    "--demo-ink": activeDemo.ink,
  } as CSSProperties;

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
      window.requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "auto" }));
    }
  };

  const selectDemo = (index: number) => showDemoPage(index, "home", true);

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
    if (nextIndex >= 0) showDemoPage(nextIndex, (match[2] as DemoPage | undefined) ?? "home", true);
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
    <section className="bg-[#050505] text-white" style={selectorStyle}>
      <div className="sticky top-[68px] z-40 border-y border-white/10 bg-[#050505]/94 backdrop-blur-2xl">
        <div className="site-container grid min-h-24 items-center gap-5 py-4 lg:grid-cols-[12rem_1fr]">
          <div className="flex items-end justify-between gap-4 lg:block">
            <p className="text-[9px] font-semibold uppercase tracking-[0.2em] text-white/35">Interactive worlds</p>
            <h1 className="mt-1 text-3xl font-semibold leading-none tracking-[-0.055em] lg:text-4xl">Demo index <span className="font-mono text-xs font-normal text-white/30">/ 03</span></h1>
          </div>
          <div className="grid w-full grid-cols-3 gap-1.5" role="tablist" aria-label="Choose a website demo">
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
                className={`demo-selector-tab flex min-h-16 min-w-0 items-center gap-3 rounded-xl border px-3 py-3 text-left sm:px-4 ${activeIndex === index ? "is-active" : ""}`}
              >
                <span className="hidden font-mono text-[9px] opacity-45 sm:block">0{index + 1}</span>
                <span className="min-w-0"><span className="block truncate text-xs font-semibold sm:text-sm">{demo.name}</span><span className="mt-1 hidden text-[8px] uppercase tracking-[0.12em] opacity-55 sm:block">{demo.type}</span></span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="site-container py-5 sm:py-8">
        <div
          id="demo-panel"
          role="tabpanel"
          aria-labelledby={`demo-tab-${activeDemo.id}`}
          tabIndex={0}
          onClickCapture={handleDemoNavigation}
          className="demo-switch-in scroll-mt-36 overflow-hidden rounded-[clamp(1rem,2.2vw,2rem)] border border-white/12 shadow-[0_40px_150px_rgba(0,0,0,.55)]"
          key={`${activeDemo.id}-${activePage}`}
        >
          {activePage === "about" ? <DemoAboutPage demo={activeDemo.id} />
            : activePage === "faq" ? <DemoFaqPage demo={activeDemo.id} />
              : activePage === "pricing" ? <DemoPricingPage demo={activeDemo.id} />
                : activePage === "contact" ? <DemoContactPage demo={activeDemo.id} />
                  : activePage === "booking" ? <DemoBookingPage demo={activeDemo.id} />
                    : activeIndex === 0 ? <MossSite />
                      : activeIndex === 1 ? <NorthlineSite />
                        : <SeraSite />}
        </div>
      </div>
    </section>
  );
}
