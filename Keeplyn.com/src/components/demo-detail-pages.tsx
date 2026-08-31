import Link from "next/link";
import { NorthlineAppointmentPicker } from "./northline-appointment-picker";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  Clock3,
  Mail,
  MapPin,
  Phone,
} from "lucide-react";

export const demoSlugs = ["moss", "northline", "sera"] as const;

export type DemoSlug = (typeof demoSlugs)[number];

export function isDemoSlug(value: string): value is DemoSlug {
  return demoSlugs.includes(value as DemoSlug);
}

const mossPackages = [
  {
    name: "Planting plan",
    price: "$1,800",
    detail: "A focused planting direction for one established outdoor space.",
    features: ["Site walk and light study", "Custom plant palette", "Placement plan", "Care notes"],
  },
  {
    name: "Garden design",
    price: "$4,800",
    detail: "A complete design for a courtyard, front garden, or compact backyard.",
    features: ["Concept and material plan", "Planting design", "Lighting direction", "Two design revisions"],
  },
  {
    name: "Full landscape",
    price: "$12k+",
    detail: "A ground-up landscape system carried from first sketch through installation.",
    features: ["Full property master plan", "Builder-ready documents", "Sourcing and contractor support", "First-year garden review"],
  },
];

const northlinePrices = [
  {
    name: "New patient visit",
    price: "$195",
    detail: "A generous first appointment with imaging, exam, and a written care plan.",
    features: ["90-minute appointment", "Digital imaging", "Comprehensive exam", "Plain-language treatment plan"],
  },
  {
    name: "Preventive visit",
    price: "$165",
    detail: "Routine cleaning and prevention, paced around your comfort.",
    features: ["Professional cleaning", "Gum health screening", "Oral cancer screening", "Personal home-care guidance"],
  },
  {
    name: "Northline plan",
    price: "$39/mo",
    detail: "Simple preventive care for patients without dental insurance.",
    features: ["Two preventive visits", "Annual imaging", "Emergency exam", "15% off restorative care"],
  },
];

const seraPackages = [
  {
    name: "Morning table",
    price: "$96",
    detail: "An easy pastry spread for eight early risers.",
    features: ["Eight mixed pastries", "One country loaf", "Seasonal jam", "Compostable serviceware"],
  },
  {
    name: "Office spread",
    price: "$180",
    detail: "Breakfast for a team of fifteen, packed and ready to share.",
    features: ["Fifteen mixed pastries", "Two savory focaccias", "Batch-brew coffee", "Local delivery"],
  },
  {
    name: "Celebration bake",
    price: "$260",
    detail: "A generous, custom assortment for gatherings up to twenty-four.",
    features: ["Seasonal pastry centerpiece", "Two bread selections", "Sweet and savory mix", "Custom menu card"],
  },
];

export function MossHeader({ active }: { active: "home" | "pricing" | "contact" }) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[#203126]/20 px-5 py-5 sm:px-9">
        <Link href="/demos/moss" className="text-lg font-semibold tracking-[-0.04em]">Moss &amp; Mortar</Link>
        <nav className="order-3 flex w-full items-center gap-6 text-[10px] font-semibold uppercase tracking-[0.14em] sm:order-none sm:w-auto sm:gap-7" aria-label="Moss & Mortar navigation">
          <Link href="/demos/moss" aria-current={active === "home" ? "page" : undefined} className={active === "home" ? "underline underline-offset-4" : ""}>Home</Link>
          <Link href="/demos/moss/pricing" aria-current={active === "pricing" ? "page" : undefined} className={active === "pricing" ? "underline underline-offset-4" : ""}>Pricing</Link>
          <Link href="/demos/moss/contact" aria-current={active === "contact" ? "page" : undefined} className={active === "contact" ? "underline underline-offset-4" : ""}>Contact</Link>
        </nav>
        <Link href="/demos/moss/contact" className="border border-[#203126] px-4 py-2 text-xs font-semibold">Start a garden</Link>
    </header>
  );
}

export function NorthlineHeader({ active }: { active: "home" | "pricing" | "contact" }) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 px-5 py-5 sm:px-9">
        <Link href="/demos/northline" className="text-lg font-semibold tracking-[-0.04em]">northline<span className="text-[#ff725e]">●</span></Link>
        <nav className="order-3 flex w-full items-center gap-6 text-[10px] font-semibold uppercase tracking-[0.13em] md:order-none md:w-auto md:gap-7" aria-label="Northline navigation">
          <Link href="/demos/northline" aria-current={active === "home" ? "page" : undefined} className={active === "home" ? "text-[#ff725e]" : ""}>Home</Link>
          <Link href="/demos/northline/pricing" aria-current={active === "pricing" ? "page" : undefined} className={active === "pricing" ? "text-[#ff725e]" : ""}>Pricing</Link>
          <Link href="/demos/northline/contact" aria-current={active === "contact" ? "page" : undefined} className={active === "contact" ? "text-[#ff725e]" : ""}>Book appointment</Link>
        </nav>
        <Link href="/demos/northline/contact" className="rounded-full bg-[#173a5a] px-5 py-2.5 text-xs font-semibold text-white">Book appointment</Link>
    </header>
  );
}

export function SeraHeader({ active }: { active: "home" | "pricing" | "contact" }) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[#5d2d26]/18 px-5 py-5 sm:px-9">
        <Link href="/demos/sera" className="font-serif text-3xl italic">Sera</Link>
        <nav className="order-3 flex w-full items-center gap-6 text-[10px] font-semibold uppercase tracking-[0.14em] sm:order-none sm:w-auto sm:gap-7" aria-label="Sera navigation">
          <Link href="/demos/sera" aria-current={active === "home" ? "page" : undefined} className={active === "home" ? "text-[#ff765f]" : ""}>Home</Link>
          <Link href="/demos/sera/pricing" aria-current={active === "pricing" ? "page" : undefined} className={active === "pricing" ? "text-[#ff765f]" : ""}>Pricing</Link>
          <Link href="/demos/sera/contact" aria-current={active === "contact" ? "page" : undefined} className={active === "contact" ? "text-[#ff765f]" : ""}>Contact</Link>
        </nav>
        <p className="text-[10px] font-semibold uppercase tracking-[0.13em]">Open 7—2</p>
    </header>
  );
}

function PackageFeatures({ features, iconClassName }: { features: string[]; iconClassName: string }) {
  return (
    <ul className="mt-8 space-y-3">
      {features.map((feature) => (
        <li key={feature} className="flex items-start gap-3 text-sm leading-6">
          <Check className={`mt-1 size-4 shrink-0 ${iconClassName}`} aria-hidden="true" />
          <span>{feature}</span>
        </li>
      ))}
    </ul>
  );
}

function MossPricing() {
  return (
    <div className="min-h-svh bg-[#dfe5d6] text-[#203126]">
      <MossHeader active="pricing" />
      <div>
        <section className="px-6 py-20 sm:px-10 lg:px-14 lg:py-28">
          <div className="mx-auto max-w-[92rem]">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#203126]/52">Design services · Northern California</p>
            <h1 className="mt-6 max-w-6xl text-[clamp(4rem,9vw,8.5rem)] font-semibold leading-[0.8] tracking-[-0.085em]">A garden plan with room to grow.</h1>
            <p className="mt-8 max-w-xl text-base leading-7 text-[#203126]/64">Every engagement starts with the ground, the season, and the way you want to live outside.</p>
          </div>
        </section>

        <section className="border-y border-[#203126]/20 bg-[#edf1e9] px-6 py-20 sm:px-10 lg:px-14 lg:py-28">
          <div className="mx-auto grid max-w-[92rem] gap-5 lg:grid-cols-3">
            {mossPackages.map((plan, index) => (
              <article key={plan.name} className={`flex min-h-[34rem] flex-col border border-[#203126]/20 p-7 sm:p-9 ${index === 1 ? "bg-[#203126] text-[#edf1e9]" : "bg-[#dfe5d6]"}`}>
                <p className={`text-[10px] uppercase tracking-[0.16em] ${index === 1 ? "text-[#c9ff3b]" : "text-[#203126]/45"}`}>0{index + 1}</p>
                <h2 className="mt-10 text-4xl font-semibold tracking-[-0.06em]">{plan.name}</h2>
                <p className={`mt-4 text-sm leading-6 ${index === 1 ? "text-white/58" : "text-[#203126]/58"}`}>{plan.detail}</p>
                <p className="mt-9 text-6xl font-semibold tracking-[-0.08em]">{plan.price}</p>
                <PackageFeatures features={plan.features} iconClassName={index === 1 ? "text-[#c9ff3b]" : "text-[#203126]"} />
                <Link href="/demos/moss/contact" className={`mt-auto flex items-center justify-between border-t pt-5 text-sm font-semibold ${index === 1 ? "border-white/18" : "border-[#203126]/20"}`}>Start a conversation <ArrowRight className="size-4" aria-hidden="true" /></Link>
              </article>
            ))}
          </div>
        </section>

        <section className="px-6 py-20 sm:px-10 lg:px-14 lg:py-28">
          <div className="mx-auto grid max-w-[92rem] gap-10 lg:grid-cols-[0.42fr_0.58fr]">
            <h2 className="text-5xl font-semibold leading-[0.9] tracking-[-0.07em] sm:text-7xl">Clear scope. Living result.</h2>
            <div className="grid gap-6 sm:grid-cols-2">
              <p className="border-t border-[#203126]/20 pt-5 text-sm leading-7 text-[#203126]/62">Construction, permitting, specialty engineering, and plant installation are quoted separately after the design direction is approved.</p>
              <p className="border-t border-[#203126]/20 pt-5 text-sm leading-7 text-[#203126]/62">A 50% design deposit reserves your start date. The balance is split across design milestones.</p>
            </div>
          </div>
        </section>
      </div>
      <footer className="flex flex-col justify-between gap-4 border-t border-[#203126]/20 px-6 py-7 text-xs text-[#203126]/52 sm:flex-row sm:px-10 lg:px-14"><span>Moss &amp; Mortar</span><Link href="/demos/moss/contact">Begin a project</Link><span>© 2026</span></footer>
    </div>
  );
}

function NorthlinePricing() {
  return (
    <div className="min-h-svh bg-[#f3f7fb] text-[#173a5a]">
      <NorthlineHeader active="pricing" />
      <div className="px-5 pb-10 sm:px-9">
        <section className="mx-auto max-w-[92rem] overflow-hidden rounded-[2rem] bg-[#173a5a] px-7 py-16 text-white sm:px-12 sm:py-24 lg:px-16">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#ff9a89]">Self-pay pricing</p>
          <h1 className="mt-6 max-w-5xl text-[clamp(4rem,9vw,8.5rem)] font-semibold leading-[0.82] tracking-[-0.085em]">Clear costs. No surprises.</h1>
          <p className="mt-8 max-w-2xl text-base leading-7 text-white/62">We review every cost before care begins and help you use insurance benefits without letting them drive the plan.</p>
        </section>

        <section className="mx-auto grid max-w-[92rem] gap-5 py-20 lg:grid-cols-3 lg:py-28">
          {northlinePrices.map((plan, index) => (
            <article key={plan.name} className={`flex min-h-[33rem] flex-col rounded-[1.75rem] border p-7 sm:p-9 ${index === 2 ? "border-[#ff725e] bg-[#fff0ec]" : "border-[#173a5a]/12 bg-white"}`}>
              <span className="grid size-10 place-items-center rounded-full bg-[#dbeaf6] text-xs font-semibold">0{index + 1}</span>
              <h2 className="mt-10 text-3xl font-semibold tracking-[-0.055em]">{plan.name}</h2>
              <p className="mt-4 text-sm leading-6 text-[#173a5a]/58">{plan.detail}</p>
              <p className="mt-9 text-6xl font-semibold tracking-[-0.08em]">{plan.price}</p>
              <PackageFeatures features={plan.features} iconClassName="text-[#ff725e]" />
              <Link href="/demos/northline/contact" className="mt-auto flex items-center justify-between rounded-full bg-[#173a5a] px-5 py-3 text-sm font-semibold text-white">Book a visit <ArrowRight className="size-4" aria-hidden="true" /></Link>
            </article>
          ))}
        </section>

        <section className="mx-auto mb-10 grid max-w-[92rem] gap-8 rounded-[2rem] bg-[#bfd9ef] p-7 sm:p-12 lg:grid-cols-[0.55fr_0.45fr] lg:items-end lg:p-16">
          <div><p className="text-[10px] uppercase tracking-[0.16em] text-[#ff725e]">Insurance and financing</p><h2 className="mt-5 text-5xl font-semibold leading-[0.92] tracking-[-0.065em] sm:text-7xl">A plan that works on paper, too.</h2></div>
          <p className="text-sm leading-7 text-[#173a5a]/62">We are in network with major PPO plans, submit claims on your behalf, and offer payment plans for restorative treatment over $750.</p>
        </section>
      </div>
      <footer className="flex flex-col justify-between gap-5 bg-[#dcebf6] px-6 py-8 text-xs sm:flex-row sm:items-center sm:px-10 lg:px-14"><span className="text-base font-semibold">northline<span className="text-[#ff725e]">●</span></span><Link href="/demos/northline/contact">Request an appointment</Link><span>(510) 555-0144</span></footer>
    </div>
  );
}

function SeraPricing() {
  return (
    <div className="min-h-svh bg-[#f6e8d8] text-[#5d2d26]">
      <SeraHeader active="pricing" />
      <div>
        <section className="px-6 py-20 sm:px-10 lg:px-14 lg:py-28">
          <div className="mx-auto max-w-[92rem]">
            <div className="grid gap-10 lg:grid-cols-[0.68fr_0.32fr] lg:items-end">
              <div><p className="font-serif text-3xl italic text-[#ff765f]">Order for the table.</p><h1 className="mt-5 text-[clamp(4.5rem,10vw,9rem)] font-semibold leading-[0.76] tracking-[-0.09em]">Good mornings, by the dozen.</h1></div>
              <p className="border-t border-[#5d2d26]/20 pt-6 text-sm leading-7 text-[#5d2d26]/62">Catering is baked to order Tuesday through Saturday. Forty-eight hours&apos; notice keeps everything unhurried.</p>
            </div>
          </div>
        </section>

        <section className="border-y border-[#5d2d26]/18 bg-[#fff6ec] px-6 py-20 sm:px-10 lg:px-14 lg:py-28">
          <div className="mx-auto grid max-w-[92rem] gap-5 lg:grid-cols-3">
            {seraPackages.map((plan, index) => (
              <article key={plan.name} className={`flex min-h-[34rem] flex-col border border-[#5d2d26]/18 p-7 sm:p-9 ${index === 1 ? "bg-[#ff765f] text-[#fff6ec]" : "bg-[#f6e8d8]"}`}>
                <p className={`font-serif text-2xl italic ${index === 1 ? "text-white" : "text-[#ff765f]"}`}>0{index + 1}</p>
                <h2 className="mt-10 text-4xl font-semibold tracking-[-0.06em]">{plan.name}</h2>
                <p className={`mt-4 text-sm leading-6 ${index === 1 ? "text-white/68" : "text-[#5d2d26]/58"}`}>{plan.detail}</p>
                <p className="mt-9 font-serif text-6xl italic tracking-[-0.06em]">{plan.price}</p>
                <PackageFeatures features={plan.features} iconClassName={index === 1 ? "text-white" : "text-[#ff765f]"} />
                <Link href="/demos/sera/contact" className={`mt-auto flex items-center justify-between border-t pt-5 text-sm font-semibold ${index === 1 ? "border-white/22" : "border-[#5d2d26]/18"}`}>Plan an order <ArrowRight className="size-4" aria-hidden="true" /></Link>
              </article>
            ))}
          </div>
        </section>

        <section className="bg-[#5d2d26] px-6 py-20 text-[#fff6ec] sm:px-10 lg:px-14 lg:py-24">
          <div className="mx-auto flex max-w-[92rem] flex-col justify-between gap-8 sm:flex-row sm:items-end">
            <div><p className="font-serif text-3xl italic text-[#ff9a86]">Need something different?</p><h2 className="mt-4 text-5xl font-semibold tracking-[-0.07em] sm:text-7xl">Let&apos;s make a menu.</h2></div>
            <Link href="/demos/sera/contact" className="inline-flex items-center gap-3 border border-white/25 px-5 py-3 text-sm font-semibold">Custom order <ArrowUpRight className="size-4" aria-hidden="true" /></Link>
          </div>
        </section>
      </div>
      <footer className="flex flex-col justify-between gap-4 bg-[#5d2d26] px-6 py-7 text-xs text-white/48 sm:flex-row sm:px-10 lg:px-14"><span className="font-serif text-xl italic text-white">Sera</span><Link href="/demos/sera/contact">Order inquiry</Link><span>© 2026</span></footer>
    </div>
  );
}

type ContactFormProps = {
  subject: string;
  serviceLabel: string;
  services: string[];
  inputClassName: string;
  buttonClassName: string;
};

function ContactForm({ subject, serviceLabel, services, inputClassName, buttonClassName }: ContactFormProps) {
  return (
    <form action="mailto:hello@keeplyn.com" method="post" encType="text/plain" className="grid gap-5">
      <input type="hidden" name="subject" value={subject} />
      <div className="grid gap-5 sm:grid-cols-2">
        <label className="grid gap-2 text-xs font-semibold">Name<input required autoComplete="name" name="name" className={inputClassName} placeholder="Your name" /></label>
        <label className="grid gap-2 text-xs font-semibold">Email<input required autoComplete="email" name="email" type="email" className={inputClassName} placeholder="you@example.com" /></label>
      </div>
      <label className="grid gap-2 text-xs font-semibold">{serviceLabel}
        <select name="service" className={inputClassName} defaultValue="">
          <option value="" disabled>Choose one</option>
          {services.map((service) => <option key={service}>{service}</option>)}
        </select>
      </label>
      <label className="grid gap-2 text-xs font-semibold">Tell us a little more<textarea required name="message" rows={6} className={`${inputClassName} resize-y`} placeholder="Timing, priorities, and anything else we should know." /></label>
      <button type="submit" className={`flex items-center justify-between px-5 py-4 text-sm font-semibold ${buttonClassName}`}>Send inquiry <ArrowUpRight className="size-4" aria-hidden="true" /></button>
    </form>
  );
}

function MossContact() {
  return (
    <div className="min-h-svh bg-[#dfe5d6] text-[#203126]">
      <MossHeader active="contact" />
      <div className="px-6 py-16 sm:px-10 lg:px-14 lg:py-24">
        <div className="mx-auto max-w-[92rem]">
          <div className="grid gap-14 lg:grid-cols-[0.48fr_0.52fr]">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#203126]/52">Now booking autumn 2026</p>
              <h1 className="mt-6 text-[clamp(4rem,8vw,8rem)] font-semibold leading-[0.8] tracking-[-0.085em]">Tell us about the life outside.</h1>
              <p className="mt-8 max-w-md text-base leading-7 text-[#203126]/62">Share the space, the season, and what you want to make possible. We&apos;ll reply within two working days.</p>
              <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
                <div className="border-t border-[#203126]/20 pt-5"><MapPin className="size-5" /><p className="mt-4 text-sm leading-6 text-[#203126]/62">Sacramento · Davis<br />San Francisco Bay Area</p></div>
                <div className="border-t border-[#203126]/20 pt-5"><Mail className="size-5" /><p className="mt-4 text-sm leading-6 text-[#203126]/62">studio@mossandmortar.example<br />Replies in 2 working days</p></div>
              </div>
            </div>
            <div className="border border-[#203126]/20 bg-[#edf1e9] p-6 sm:p-9 lg:p-12">
              <ContactForm subject="Moss & Mortar demo inquiry" serviceLabel="What are you considering?" services={["Planting plan", "Garden design", "Full landscape", "Not sure yet"]} inputClassName="min-h-12 w-full border border-[#203126]/22 bg-transparent px-4 py-3 text-sm outline-none placeholder:text-[#203126]/35 focus:border-[#203126]" buttonClassName="bg-[#203126] text-[#edf1e9]" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function NorthlineContact() {
  return (
    <div className="min-h-svh bg-[#f3f7fb] text-[#173a5a]">
      <NorthlineHeader active="contact" />
      <div className="px-5 pb-10 sm:px-9">
        <div className="mx-auto grid max-w-[92rem] overflow-hidden rounded-[2rem] bg-white lg:grid-cols-[0.46fr_0.54fr]">
          <section className="bg-[#173a5a] p-7 text-white sm:p-12 lg:p-16">
            <p className="text-[10px] uppercase tracking-[0.16em] text-[#ff9a89]">Accepting new patients</p>
            <h1 className="mt-6 text-[clamp(4rem,8vw,7.5rem)] font-semibold leading-[0.82] tracking-[-0.085em]">Let&apos;s make your next visit easier.</h1>
            <div className="mt-14 space-y-6 border-t border-white/16 pt-7 text-sm text-white/65">
              <p className="flex gap-4"><Phone className="size-5 shrink-0 text-[#ff725e]" aria-hidden="true" />(510) 555-0144</p>
              <p className="flex gap-4"><MapPin className="size-5 shrink-0 text-[#ff725e]" aria-hidden="true" />411 Grand Avenue · Oakland, CA</p>
              <p className="flex gap-4"><Clock3 className="size-5 shrink-0 text-[#ff725e]" aria-hidden="true" />Monday—Thursday · 8am—5pm</p>
            </div>
          </section>
          <section className="p-7 sm:p-12 lg:p-16">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#ff725e]">Book an appointment</p>
            <h2 className="mt-5 text-4xl font-semibold tracking-[-0.06em] sm:text-5xl">Choose a time that works.</h2>
            <div className="mt-10">
              <NorthlineAppointmentPicker />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function SeraContact() {
  return (
    <div className="min-h-svh bg-[#f6e8d8] text-[#5d2d26]">
      <SeraHeader active="contact" />
      <div className="px-6 py-16 sm:px-10 lg:px-14 lg:py-24">
        <div className="mx-auto max-w-[92rem]">
          <div className="grid gap-14 lg:grid-cols-[0.5fr_0.5fr]">
            <div>
              <p className="font-serif text-3xl italic text-[#ff765f]">Save us a place.</p>
              <h1 className="mt-5 text-[clamp(4.5rem,9vw,8.5rem)] font-semibold leading-[0.75] tracking-[-0.09em]">Bread for whatever&apos;s next.</h1>
              <p className="mt-8 max-w-md text-base leading-7 text-[#5d2d26]/62">Tell us how many people, when you need it, and what kind of morning you&apos;re planning.</p>
              <div className="mt-14 grid gap-5 sm:grid-cols-2">
                <div className="border-t border-[#5d2d26]/18 pt-5"><MapPin className="size-5 text-[#ff765f]" /><p className="mt-4 text-sm leading-6 text-[#5d2d26]/62">207 Pine Avenue<br />Long Beach, CA</p></div>
                <div className="border-t border-[#5d2d26]/18 pt-5"><Clock3 className="size-5 text-[#ff765f]" /><p className="mt-4 text-sm leading-6 text-[#5d2d26]/62">Tuesday—Sunday<br />7am—2pm</p></div>
              </div>
            </div>
            <div className="border border-[#5d2d26]/18 bg-[#fff6ec] p-6 sm:p-9 lg:p-12">
              <ContactForm subject="Sera demo order inquiry" serviceLabel="What are you planning?" services={["Morning table", "Office spread", "Celebration bake", "Custom order"]} inputClassName="min-h-12 w-full border border-[#5d2d26]/20 bg-transparent px-4 py-3 text-sm outline-none placeholder:text-[#5d2d26]/35 focus:border-[#ff765f]" buttonClassName="bg-[#ff765f] text-white" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function DemoPricingPage({ demo }: { demo: DemoSlug }) {
  if (demo === "moss") return <MossPricing />;
  if (demo === "northline") return <NorthlinePricing />;
  return <SeraPricing />;
}

export function DemoContactPage({ demo }: { demo: DemoSlug }) {
  if (demo === "moss") return <MossContact />;
  if (demo === "northline") return <NorthlineContact />;
  return <SeraContact />;
}
