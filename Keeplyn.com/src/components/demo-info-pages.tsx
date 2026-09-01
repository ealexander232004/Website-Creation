import Image from "next/image";
import Link from "next/link";
import { ArrowRight, ArrowUpRight, Move3D, Plus } from "lucide-react";
import { MossHeader, NorthlineHeader, SeraHeader, type DemoSlug } from "@/components/demo-detail-pages";
import { DemoWorld } from "@/components/demo-world-slot";
import { MossVines, SeraProofingField } from "@/components/demo-visual-systems";

type FaqItem = {
  question: string;
  answer: string;
};

function FaqList({ items, itemClassName, answerClassName }: { items: FaqItem[]; itemClassName: string; answerClassName: string }) {
  return (
    <div>
      {items.map((item, index) => (
        <details key={item.question} className={`group border-t ${itemClassName}`} open={index === 0}>
          <summary className="flex cursor-pointer list-none items-center justify-between gap-6 py-6 text-left text-xl font-semibold tracking-[-0.035em] marker:hidden sm:text-2xl">
            <span>{item.question}</span>
            <Plus className="size-5 shrink-0 transition-transform duration-300 group-open:rotate-45" aria-hidden="true" />
          </summary>
          <p className={`max-w-2xl pb-7 text-sm leading-7 ${answerClassName}`}>{item.answer}</p>
        </details>
      ))}
    </div>
  );
}

const mossFaqs: FaqItem[] = [
  { question: "What kinds of spaces do you design?", answer: "Courtyards, front gardens, backyards, and full residential landscapes across Northern California." },
  { question: "Can you work with an existing garden?", answer: "Yes. We keep what is thriving, edit what is not, and design the next layer around mature plants and real site conditions." },
  { question: "How long does design take?", answer: "A focused planting plan takes about four weeks. Full landscapes typically take eight to twelve weeks before construction." },
  { question: "Do you manage installation?", answer: "We can source plants, coordinate trusted installers, review the work, and return for a first-season garden check." },
  { question: "Where does a project begin?", answer: "With a short consultation, a few site photos, and an honest conversation about budget, timing, and how you want to live outside." },
];

const northlineFaqs: FaqItem[] = [
  { question: "Do you accept insurance?", answer: "We work with major PPO plans, check benefits before treatment, and show insurance and self-pay costs up front." },
  { question: "What happens at a first visit?", answer: "A conversation, comfortable digital imaging, a comprehensive exam, and a clear written plan. We reserve ninety unhurried minutes." },
  { question: "Can you help with dental anxiety?", answer: "Absolutely. Tell us what has felt difficult before. We agree on pause signals, explain each step, and move at your pace." },
  { question: "Do you see children?", answer: "Yes. Northline welcomes families and adapts visits for young patients, sensory needs, and first-ever appointments." },
  { question: "What if I have an urgent problem?", answer: "Call early. Same-day spaces are held Monday through Thursday, with after-hours triage for existing patients." },
];

const seraFaqs: FaqItem[] = [
  { question: "Can I preorder the daily bake?", answer: "Country loaves and pastry boxes can be reserved forty-eight hours ahead. A small walk-in batch always stays on the shelf." },
  { question: "What time do you sell out?", answer: "It changes with the day. Bread usually lasts through noon; laminated pastry tends to move fastest before nine." },
  { question: "Do you accommodate allergies?", answer: "Our kitchen handles wheat, dairy, eggs, sesame, and nuts. We label every item, but cannot promise an allergen-free environment." },
  { question: "Is local delivery available?", answer: "Yes for catering orders over $150 within central Long Beach. Smaller orders are ready for pickup from seven." },
  { question: "Do you bake for wholesale partners?", answer: "A small number of restaurants receive bread Tuesday through Saturday. Send an inquiry with volume and timing." },
];

function MossAbout() {
  return (
    <div className="moss-world min-h-svh overflow-hidden bg-[#dfe5d6] text-[#203126]">
      <MossHeader active="about" />
      <section className="grid min-h-[44rem] bg-[#14241a] text-[#f3f5ed] lg:grid-cols-[0.46fr_0.54fr]">
        <div className="relative z-10 flex flex-col justify-between border-b border-white/10 p-7 sm:p-12 lg:border-r lg:border-b-0 lg:p-16">
          <div className="flex justify-between gap-8 text-[10px] uppercase tracking-[0.19em] text-[#c9ff3b]"><span>Studio / field</span><span className="text-right text-white/35">Sacramento<br />California</span></div>
          <div className="py-20 lg:py-10">
            <h1 className="text-[clamp(4.7rem,8.5vw,8.8rem)] font-semibold leading-[0.73] tracking-[-0.095em]">Ground first.<br /><span className="font-serif font-normal italic text-[#c9ff3b]">Always.</span></h1>
            <p className="mt-9 max-w-md text-sm leading-7 text-white/54">Resilient gardens shaped around light, weather, and the way people actually live outside.</p>
          </div>
          <Link href="/demos/moss/pricing" className="group inline-flex w-fit items-center gap-3 text-sm font-semibold text-[#c9ff3b]">Explore the scope <ArrowRight className="size-4 transition-transform group-hover:translate-x-1.5" aria-hidden="true" /></Link>
        </div>
        <div className="moss-world-stage demo-world-stage relative min-h-[32rem] overflow-hidden">
          <MossVines variant="canopy" className="absolute inset-0 z-0 size-full opacity-26" />
          <DemoWorld variant="moss" className="relative z-[2] size-full" />
          <div className="demo-stage-label right-7 top-7"><Move3D className="size-3.5" aria-hidden="true" /> The studio terrain</div>
        </div>
      </section>

      <section className="px-5 py-20 sm:px-9 lg:px-12 lg:py-28">
        <div className="mx-auto grid max-w-[92rem] gap-5 lg:grid-cols-12">
          <figure className="moss-depth-card relative min-h-[34rem] overflow-hidden rounded-[2.5rem] lg:col-span-7">
            <Image src="/demos/moss-garden-passage.png" alt="A stone passage threaded through a fern garden" fill sizes="(min-width: 1024px) 58vw, 100vw" className="object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#102016]/72 via-transparent to-transparent" />
            <figcaption className="absolute bottom-8 left-8 max-w-md text-3xl font-semibold leading-tight tracking-[-0.045em] text-white">We draw the structure. Weather writes the rest.</figcaption>
          </figure>
          <article className="moss-depth-card flex min-h-[34rem] flex-col justify-between rounded-[2.5rem] border border-[#203126]/16 bg-[#edf1e9] p-8 lg:col-span-5 lg:p-11">
            <p className="text-[10px] font-semibold uppercase tracking-[0.19em] text-[#203126]/42">How the studio thinks</p>
            <blockquote className="font-serif text-5xl italic leading-[1.02] tracking-[-0.05em] sm:text-6xl">“A garden should feel discovered, not installed.”</blockquote>
            <div className="grid grid-cols-2 gap-5 border-t border-[#203126]/16 pt-6"><div><strong className="text-4xl tracking-[-0.06em]">12</strong><p className="mt-1 text-xs text-[#203126]/52">gardens each year</p></div><div><strong className="text-4xl tracking-[-0.06em]">4</strong><p className="mt-1 text-xs text-[#203126]/52">seasons considered</p></div></div>
          </article>
        </div>
      </section>

      <section className="bg-[#203126] px-6 py-20 text-[#edf1e9] sm:px-10 lg:px-14">
        <div className="mx-auto flex max-w-[92rem] flex-col justify-between gap-10 sm:flex-row sm:items-end"><h2 className="max-w-4xl text-5xl font-semibold leading-[0.88] tracking-[-0.07em] sm:text-8xl">A living system,<br />not a reveal.</h2><Link href="/demos/moss/booking" className="inline-flex items-center gap-3 text-sm font-semibold text-[#c9ff3b]">Start a garden <ArrowUpRight className="size-4" aria-hidden="true" /></Link></div>
      </section>
    </div>
  );
}

function MossFaq() {
  return (
    <div className="moss-world min-h-svh overflow-hidden bg-[#dfe5d6] text-[#203126]">
      <MossHeader active="faq" />
      <section className="px-5 py-10 sm:px-9 lg:px-12 lg:py-14">
        <div className="mx-auto grid max-w-[92rem] overflow-hidden rounded-[2.5rem] border border-[#203126]/14 bg-[#edf1e9] shadow-[0_34px_90px_rgba(23,38,28,.14)] lg:grid-cols-[0.42fr_0.58fr]">
          <div className="moss-world-stage demo-world-stage relative min-h-[31rem] overflow-hidden lg:min-h-0"><DemoWorld variant="moss" className="relative z-[2] size-full" /><div className="relative z-10 p-8 sm:p-11"><p className="text-[10px] uppercase tracking-[0.19em] text-[#c9ff3b]">Field notes / FAQ</p><h1 className="mt-6 text-[clamp(4.5rem,7.5vw,7.5rem)] font-semibold leading-[0.76] tracking-[-0.09em] text-white">Before we<br /><span className="font-serif font-normal italic text-[#c9ff3b]">dig in.</span></h1></div></div>
          <div className="p-7 sm:p-11 lg:p-14"><FaqList items={mossFaqs} itemClassName="border-[#203126]/18" answerClassName="text-[#203126]/62" /><Link href="/demos/moss/contact" className="mt-9 inline-flex items-center gap-3 rounded-full bg-[#203126] px-5 py-3 text-sm font-semibold text-[#edf1e9]">Ask the studio <ArrowRight className="size-4" aria-hidden="true" /></Link></div>
        </div>
      </section>
    </div>
  );
}

function NorthlineAbout() {
  return (
    <div className="northline-world min-h-svh overflow-hidden bg-[#f3f7fb] text-[#173a5a]">
      <NorthlineHeader active="about" />
      <section className="px-4 pb-5 sm:px-7 sm:pb-8">
        <div className="northline-depth-card mx-auto grid min-h-[44rem] max-w-[92rem] overflow-hidden rounded-[2.75rem] bg-[#173a5a] text-white lg:grid-cols-[0.44fr_0.56fr]">
          <div className="relative z-10 flex flex-col justify-between border-b border-white/12 p-8 sm:p-12 lg:border-r lg:border-b-0 lg:p-16"><p className="text-[10px] uppercase tracking-[0.19em] text-[#ff9a89]">People before procedure</p><div className="py-20 lg:py-8"><h1 className="text-[clamp(4.6rem,8vw,8rem)] font-semibold leading-[0.77] tracking-[-0.09em]">Care,<br />clearly.</h1><p className="mt-8 max-w-md text-sm leading-7 text-white/56">Calm rooms, honest choices, and enough time to make the next step feel manageable.</p></div><Link href="/demos/northline/booking" className="inline-flex w-fit items-center gap-3 rounded-full bg-[#ff725e] px-5 py-3 text-sm font-semibold">Meet Northline <ArrowRight className="size-4" aria-hidden="true" /></Link></div>
          <div className="northline-world-stage demo-world-stage relative min-h-[32rem] overflow-hidden"><div className="northline-stage-grid absolute inset-0" aria-hidden="true" /><DemoWorld variant="northline" className="relative z-[2] size-full" /><div className="demo-stage-label right-7 top-7 text-[#173a5a]"><Move3D className="size-3.5" aria-hidden="true" /> Care, in motion</div></div>
        </div>
      </section>

      <section className="px-5 py-20 sm:px-9 lg:py-28"><div className="mx-auto grid max-w-[92rem] gap-5 lg:grid-cols-12"><figure className="northline-depth-card relative min-h-[35rem] overflow-hidden rounded-[2.5rem] lg:col-span-7"><Image src="/demos/northline-clinic.jpg" alt="A patient and clinician speaking in the Northline clinic" fill sizes="(min-width: 1024px) 58vw, 100vw" className="object-cover" /><div className="absolute inset-0 bg-gradient-to-t from-[#173a5a]/68 via-transparent to-transparent" /><figcaption className="absolute bottom-8 left-8 max-w-lg text-3xl font-semibold leading-tight tracking-[-0.045em] text-white">The best technology in the room should make the room feel more human.</figcaption></figure><article className="northline-depth-card flex min-h-[35rem] flex-col justify-between rounded-[2.5rem] bg-[#dceef8] p-8 lg:col-span-5 lg:p-11"><p className="text-[10px] uppercase tracking-[0.19em] text-[#c9483c]">Built around comfort</p><p className="text-5xl font-semibold leading-[0.94] tracking-[-0.065em] sm:text-6xl">Longer visits.<br />Quieter rooms.<br />Clearer choices.</p><div className="flex items-center justify-between border-t border-[#173a5a]/14 pt-6"><span className="text-sm text-[#173a5a]/52">Oakland · since 2018</span><Link href="/demos/northline/faq" aria-label="Read Northline frequently asked questions" className="grid size-12 place-items-center rounded-full bg-[#173a5a] text-white"><ArrowUpRight className="size-5" aria-hidden="true" /></Link></div></article></div></section>
    </div>
  );
}

function NorthlineFaq() {
  return (
    <div className="northline-world min-h-svh overflow-hidden bg-[#f3f7fb] text-[#173a5a]">
      <NorthlineHeader active="faq" />
      <section className="px-4 pb-8 sm:px-7"><div className="northline-depth-card mx-auto grid max-w-[92rem] overflow-hidden rounded-[2.75rem] bg-white lg:grid-cols-[0.42fr_0.58fr]"><div className="northline-world-stage demo-world-stage relative min-h-[31rem] overflow-hidden lg:min-h-0"><div className="northline-stage-grid absolute inset-0" aria-hidden="true" /><DemoWorld variant="northline" className="relative z-[2] size-full" /><div className="relative z-10 p-8 sm:p-11"><p className="text-[10px] uppercase tracking-[0.19em] text-[#c9483c]">Questions / answers</p><h1 className="mt-6 text-[clamp(4.4rem,7.5vw,7.5rem)] font-semibold leading-[0.78] tracking-[-0.085em]">Feel<br />ready.</h1></div></div><div className="p-7 sm:p-11 lg:p-14"><FaqList items={northlineFaqs} itemClassName="border-[#173a5a]/14" answerClassName="text-[#173a5a]/58" /><Link href="/demos/northline/contact" className="mt-9 inline-flex items-center gap-3 rounded-full bg-[#173a5a] px-5 py-3 text-sm font-semibold text-white">Ask the team <ArrowRight className="size-4" aria-hidden="true" /></Link></div></div></section>
    </div>
  );
}

function SeraAbout() {
  return (
    <div className="sera-world min-h-svh overflow-hidden bg-[#f6e8d8] text-[#5d2d26]">
      <SeraHeader active="about" />
      <section className="grid min-h-[45rem] lg:grid-cols-[0.56fr_0.44fr]">
        <div className="sera-world-stage demo-world-stage relative min-h-[33rem] overflow-hidden"><SeraProofingField className="absolute inset-0 z-0 size-full opacity-12" /><DemoWorld variant="sera" className="relative z-[2] size-full" /><div className="demo-stage-label left-7 top-7 border-white/20 bg-[#5d2d26]/45"><Move3D className="size-3.5" aria-hidden="true" /> The proofing bloom</div></div>
        <div className="flex flex-col justify-between border-t border-[#5d2d26]/12 p-8 sm:p-12 lg:border-t-0 lg:border-l lg:p-16"><p className="font-serif text-3xl italic text-[#ff765f]">Long fermentation. Short menu.</p><div className="py-20 lg:py-8"><h1 className="text-[clamp(4.8rem,8.6vw,8.8rem)] font-semibold leading-[0.7] tracking-[-0.095em]">Made<br />by time.</h1><p className="mt-9 max-w-md text-sm leading-7 text-[#5d2d26]/58">Naturally leavened bread and the first quiet hours of the day, baked into one neighborhood ritual.</p></div><Link href="/demos/sera/pricing" className="group inline-flex w-fit items-center gap-3 text-sm font-semibold">Plan a table <ArrowRight className="size-4 transition-transform group-hover:translate-x-1.5" aria-hidden="true" /></Link></div>
      </section>
      <section className="bg-[#fff6ec] px-5 py-20 sm:px-9 lg:px-12 lg:py-28"><div className="mx-auto grid max-w-[92rem] gap-5 lg:grid-cols-[0.62fr_0.38fr]"><article className="sera-depth-card flex min-h-[31rem] flex-col justify-between rounded-[2.5rem] bg-[#ff765f] p-8 text-[#fff6ec] lg:p-12"><p className="text-[10px] uppercase tracking-[0.19em] text-white/62">The whole recipe</p><blockquote className="font-serif text-6xl italic leading-[1.02] tracking-[-0.055em] sm:text-8xl">“Patience,<br />then heat.”</blockquote><p className="text-sm text-white/62">Flour · water · salt · time</p></article><div className="grid gap-5"><article className="sera-depth-card flex min-h-[14rem] items-end justify-between rounded-[2.5rem] border border-[#5d2d26]/14 bg-[#f6e8d8] p-8"><div><strong className="font-serif text-6xl italic text-[#ff765f]">18h</strong><p className="mt-2 text-xs uppercase tracking-[0.14em]">average ferment</p></div></article><article className="sera-depth-card flex min-h-[14rem] items-end justify-between rounded-[2.5rem] bg-[#f4c96f] p-8"><div><strong className="font-serif text-6xl italic">7:00</strong><p className="mt-2 text-xs uppercase tracking-[0.14em]">doors open</p></div><Link href="/demos/sera/faq" aria-label="Read Sera frequently asked questions" className="grid size-12 place-items-center rounded-full bg-[#5d2d26] text-white"><ArrowUpRight className="size-5" aria-hidden="true" /></Link></article></div></div></section>
    </div>
  );
}

function SeraFaq() {
  return (
    <div className="sera-world min-h-svh overflow-hidden bg-[#f6e8d8] text-[#5d2d26]">
      <SeraHeader active="faq" />
      <section className="px-5 py-10 sm:px-9 lg:px-12 lg:py-14"><div className="sera-depth-card mx-auto grid max-w-[92rem] overflow-hidden rounded-[2.5rem] bg-[#fff6ec] lg:grid-cols-[0.42fr_0.58fr]"><div className="sera-world-stage demo-world-stage relative min-h-[31rem] overflow-hidden lg:min-h-0"><DemoWorld variant="sera" className="relative z-[2] size-full" /><div className="relative z-10 p-8 sm:p-11"><p className="font-serif text-3xl italic text-[#f4c96f]">Before breakfast.</p><h1 className="mt-5 text-[clamp(4.5rem,7.5vw,7.5rem)] font-semibold leading-[0.76] tracking-[-0.09em] text-[#fff6ec]">Good<br />to know.</h1></div></div><div className="p-7 sm:p-11 lg:p-14"><FaqList items={seraFaqs} itemClassName="border-[#5d2d26]/16" answerClassName="text-[#5d2d26]/60" /><Link href="/demos/sera/contact" className="mt-9 inline-flex items-center gap-3 rounded-full bg-[#ff765f] px-5 py-3 text-sm font-semibold text-white">Order inquiry <ArrowRight className="size-4" aria-hidden="true" /></Link></div></div></section>
    </div>
  );
}

export function DemoAboutPage({ demo }: { demo: DemoSlug }) {
  if (demo === "moss") return <MossAbout />;
  if (demo === "northline") return <NorthlineAbout />;
  return <SeraAbout />;
}

export function DemoFaqPage({ demo }: { demo: DemoSlug }) {
  if (demo === "moss") return <MossFaq />;
  if (demo === "northline") return <NorthlineFaq />;
  return <SeraFaq />;
}
