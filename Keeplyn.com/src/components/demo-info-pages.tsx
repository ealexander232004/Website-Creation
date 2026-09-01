import Link from "next/link";
import { ArrowRight, ArrowUpRight, Plus } from "lucide-react";
import { MossHeader, NorthlineHeader, SeraHeader, type DemoSlug } from "@/components/demo-detail-pages";
import { MossVines, NorthlineSignalMap, SeraProofingField } from "@/components/demo-visual-systems";

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
            <span className="flex items-center gap-5"><span className="font-mono text-[10px] font-normal opacity-45">0{index + 1}</span>{item.question}</span>
            <Plus className="size-5 shrink-0 transition-transform duration-300 group-open:rotate-45" aria-hidden="true" />
          </summary>
          <p className={`max-w-2xl pb-7 pl-10 text-sm leading-7 ${answerClassName}`}>{item.answer}</p>
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
  { question: "Do you accept insurance?", answer: "We work with major PPO plans, check benefits before treatment, and show both insurance and self-pay costs up front." },
  { question: "What happens at a first visit?", answer: "A conversation, comfortable digital imaging, a comprehensive exam, and a clear written plan. We reserve ninety unhurried minutes." },
  { question: "I am anxious about dental care. Can you help?", answer: "Absolutely. Tell us what has felt difficult before. We explain each step, agree on pause signals, and move at your pace." },
  { question: "Do you see children?", answer: "Yes. Northline welcomes families and adapts visits for young patients, sensory needs, and first-ever appointments." },
  { question: "What if I have an urgent problem?", answer: "Call early. Existing patients are held same-day spaces Monday through Thursday, with after-hours triage when needed." },
];

const seraFaqs: FaqItem[] = [
  { question: "Can I preorder the daily bake?", answer: "Country loaves and pastry boxes can be reserved forty-eight hours ahead. A small walk-in batch always stays on the shelf." },
  { question: "What time do you sell out?", answer: "It changes with the day. Bread usually lasts through noon; laminated pastry tends to move fastest before nine." },
  { question: "Do you accommodate allergies?", answer: "Our kitchen handles wheat, dairy, eggs, sesame, and nuts. We label every item, but cannot promise an allergen-free environment." },
  { question: "Is local delivery available?", answer: "Yes for catering orders over $150 within central Long Beach. Smaller orders are ready for pickup from seven." },
  { question: "Do you bake for wholesale partners?", answer: "A small number of restaurants receive bread Tuesday through Saturday. Send an inquiry with volume and delivery timing." },
];

function MossAbout() {
  return (
    <div className="moss-world min-h-svh overflow-hidden bg-[#dfe5d6] text-[#203126]">
      <MossHeader active="about" />
      <section className="relative isolate min-h-[45rem] overflow-hidden bg-[#14241a] px-6 py-16 text-[#f3f5ed] sm:px-10 lg:px-14 lg:py-24">
        <MossVines variant="canopy" className="absolute inset-0 z-0 opacity-90" />
        <div className="relative z-10 mx-auto flex min-h-[34rem] max-w-[92rem] flex-col justify-between">
          <div className="flex justify-between gap-8 text-[10px] uppercase tracking-[0.18em] text-[#c9ff3b]"><span>Studio / field</span><span className="text-right text-white/35">Sacramento<br />California</span></div>
          <div className="max-w-6xl">
            <h1 className="text-[clamp(4.7rem,10vw,10rem)] font-semibold leading-[0.72] tracking-[-0.095em]">Ground first.<br /><span className="font-serif font-normal italic text-[#c9ff3b]">Always.</span></h1>
            <div className="mt-10 flex flex-wrap items-center gap-5">
              <p className="max-w-md text-sm leading-6 text-white/58">A landscape studio making resilient, deeply lived-in gardens.</p>
              <Link href="/demos/moss/pricing" className="inline-flex items-center gap-3 border-b border-[#c9ff3b]/55 pb-2 text-sm font-semibold">See the scope <ArrowRight className="size-4" aria-hidden="true" /></Link>
            </div>
          </div>
        </div>
      </section>
      <section className="relative px-6 py-20 sm:px-10 lg:px-14 lg:py-28">
        <MossVines variant="thread" className="absolute -right-[18%] top-0 z-0 h-full w-[76%] opacity-45" />
        <div className="relative z-10 mx-auto grid max-w-[92rem] gap-4 lg:grid-cols-12">
          <article className="moss-depth-card min-h-[26rem] bg-[#203126] p-7 text-[#edf1e9] sm:p-10 lg:col-span-6"><span className="text-[10px] uppercase tracking-[0.18em] text-[#c9ff3b]">01 / Observe</span><p className="mt-28 max-w-md text-5xl font-semibold leading-[0.9] tracking-[-0.07em] sm:text-7xl">Read the land.</p></article>
          <article className="moss-depth-card min-h-[26rem] bg-[#9daa8b] p-7 sm:p-10 lg:col-span-3"><span className="text-[10px] uppercase tracking-[0.18em]">02 / Draw</span><div className="moss-topography-disc mx-auto mt-16" /><p className="mt-10 font-serif text-3xl italic">Light into line.</p></article>
          <article className="moss-depth-card relative min-h-[26rem] overflow-hidden bg-[#c9ff3b] p-7 sm:p-10 lg:col-span-3"><span className="text-[10px] uppercase tracking-[0.18em]">03 / Grow</span><div className="moss-growth-rings" /><p className="absolute bottom-9 left-9 font-serif text-3xl italic">Time finishes it.</p></article>
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
      <section className="relative isolate overflow-hidden px-6 py-16 sm:px-10 lg:px-14 lg:py-24">
        <MossVines variant="thread" className="absolute -right-[26%] -top-16 z-0 h-[44rem] w-[86%] opacity-55" />
        <div className="relative z-10 mx-auto grid max-w-[92rem] gap-14 lg:grid-cols-[0.4fr_0.6fr]">
          <div><p className="text-[10px] uppercase tracking-[0.18em] text-[#203126]/48">Field notes / FAQ</p><h1 className="mt-5 text-[clamp(4.8rem,9vw,8.5rem)] font-semibold leading-[0.75] tracking-[-0.09em]">Before we<br /><span className="font-serif font-normal italic text-[#4d6a4e]">dig in.</span></h1><Link href="/demos/moss/contact" className="mt-10 inline-flex items-center gap-3 bg-[#203126] px-5 py-3 text-sm font-semibold text-[#edf1e9] shadow-[0_20px_60px_rgba(23,38,28,.22)]">Ask the studio <ArrowRight className="size-4" /></Link></div>
          <div className="moss-depth-card bg-[#edf1e9]/90 p-6 backdrop-blur-md sm:p-9"><FaqList items={mossFaqs} itemClassName="border-[#203126]/18" answerClassName="text-[#203126]/62" /></div>
        </div>
      </section>
    </div>
  );
}

function NorthlineAbout() {
  return (
    <div className="northline-world min-h-svh overflow-hidden bg-[#f3f7fb] text-[#173a5a]">
      <NorthlineHeader active="about" />
      <section className="px-5 pb-7 sm:px-9">
        <div className="northline-depth-card relative mx-auto grid min-h-[43rem] max-w-[92rem] overflow-hidden rounded-[2.5rem] bg-[#173a5a] text-white lg:grid-cols-[0.48fr_0.52fr]">
          <div className="relative z-10 flex flex-col justify-between p-7 sm:p-12 lg:p-16"><p className="text-[10px] uppercase tracking-[0.18em] text-[#ff9a89]">People before procedure</p><div><h1 className="text-[clamp(4.6rem,9vw,8.5rem)] font-semibold leading-[0.77] tracking-[-0.09em]">Care,<br />clearly.</h1><p className="mt-8 max-w-md text-sm leading-7 text-white/58">A family practice designed around calm rooms, honest choices, and enough time.</p></div><Link href="/demos/northline/booking" className="inline-flex w-fit items-center gap-3 rounded-full bg-[#ff725e] px-5 py-3 text-sm font-semibold">Meet Northline <ArrowRight className="size-4" /></Link></div>
          <div className="relative min-h-[30rem] overflow-hidden bg-[#cfe9f5]"><NorthlineSignalMap className="absolute inset-0 size-full" /><div className="northline-glass-orb absolute left-1/2 top-1/2" /></div>
        </div>
      </section>
      <section className="px-5 py-20 sm:px-9 lg:py-28"><div className="mx-auto grid max-w-[92rem] gap-4 md:grid-cols-3">{[["01","Listen","Nothing starts until we know what matters."],["02","Show","See what we see, in plain language."],["03","Choose","Options without pressure or surprise."]].map(([number,title,copy], index)=><article key={number} className={`northline-depth-card relative min-h-[24rem] overflow-hidden rounded-[2rem] p-7 ${index===1?"bg-[#ff725e] text-white":"bg-white"}`}><span className="text-xs opacity-45">{number}</span><div className={`demo-smile-arc demo-smile-arc-${index+1} absolute right-[-12%] top-[16%]`} /><div className="absolute bottom-7 left-7 right-7"><h2 className="text-4xl font-semibold tracking-[-0.06em]">{title}</h2><p className="mt-3 max-w-xs text-sm leading-6 opacity-60">{copy}</p></div></article>)}</div></section>
    </div>
  );
}

function NorthlineFaq() {
  return (
    <div className="northline-world min-h-svh overflow-hidden bg-[#f3f7fb] text-[#173a5a]">
      <NorthlineHeader active="faq" />
      <section className="px-5 pb-10 sm:px-9"><div className="northline-depth-card mx-auto grid max-w-[92rem] overflow-hidden rounded-[2.5rem] bg-white lg:grid-cols-[0.38fr_0.62fr]"><div className="relative min-h-[32rem] overflow-hidden bg-[#cfe9f5] p-7 sm:p-12"><NorthlineSignalMap className="absolute inset-0 size-full opacity-75" /><div className="relative z-10"><p className="text-[10px] uppercase tracking-[0.18em] text-[#ff725e]">Questions / answers</p><h1 className="mt-6 text-[clamp(4.4rem,8vw,7.5rem)] font-semibold leading-[0.78] tracking-[-0.085em]">Feel<br />ready.</h1></div><Link href="/demos/northline/contact" className="absolute bottom-9 left-9 z-10 inline-flex items-center gap-3 rounded-full bg-[#173a5a] px-5 py-3 text-sm font-semibold text-white">Ask the team <ArrowRight className="size-4" /></Link></div><div className="p-7 sm:p-12 lg:p-16"><FaqList items={northlineFaqs} itemClassName="border-[#173a5a]/14" answerClassName="text-[#173a5a]/58" /></div></div></section>
    </div>
  );
}

function SeraAbout() {
  return (
    <div className="sera-world min-h-svh overflow-hidden bg-[#f6e8d8] text-[#5d2d26]">
      <SeraHeader active="about" />
      <section className="grid min-h-[46rem] lg:grid-cols-[0.56fr_0.44fr]"><div className="relative isolate overflow-hidden bg-[#5d2d26] p-7 text-[#fff6ec] sm:p-12 lg:p-16"><SeraProofingField className="absolute inset-0 z-0 size-full opacity-90" /><div className="relative z-10 flex h-full flex-col justify-between"><p className="font-serif text-3xl italic text-[#ff9a86]">Long fermentation. Short menu.</p><h1 className="text-[clamp(4.8rem,9vw,9rem)] font-semibold leading-[0.7] tracking-[-0.095em]">Made<br />by time.</h1><p className="text-xs uppercase tracking-[0.16em] text-white/42">Flour · water · salt · patience</p></div></div><div className="relative flex flex-col justify-between overflow-hidden p-7 sm:p-12 lg:p-16"><div className="sera-paper-shadow absolute right-[-8rem] top-20 size-72 rotate-12 bg-[#ff765f]" /><p className="relative z-10 max-w-md text-lg leading-8">Sera is a neighborhood bakehouse built around naturally leavened bread and the first quiet hours of the day.</p><div className="relative z-10 grid gap-3 sm:grid-cols-2"><div className="sera-depth-card bg-[#fff6ec] p-6"><span className="font-serif text-5xl italic text-[#ff765f]">18h</span><p className="mt-3 text-xs uppercase tracking-[0.14em]">Average ferment</p></div><div className="sera-depth-card bg-[#f4c96f] p-6"><span className="font-serif text-5xl italic">7:00</span><p className="mt-3 text-xs uppercase tracking-[0.14em]">Doors open</p></div></div><Link href="/demos/sera/pricing" className="relative z-10 inline-flex w-fit items-center gap-3 border-b border-[#5d2d26]/25 pb-2 text-sm font-semibold">Plan a table <ArrowRight className="size-4" /></Link></div></section>
      <section className="bg-[#ff765f] px-6 py-20 text-[#fff6ec] sm:px-10 lg:px-14"><div className="mx-auto grid max-w-[92rem] gap-6 md:grid-cols-3">{[["01","Mix","Before sunrise."],["02","Fold","Until it holds."],["03","Bake","Until it sings."]].map(([number,title,copy])=><article key={number} className="border-t border-white/28 pt-5"><span className="font-mono text-xs text-white/55">{number}</span><h2 className="mt-12 font-serif text-5xl italic">{title}</h2><p className="mt-2 text-sm text-white/60">{copy}</p></article>)}</div></section>
    </div>
  );
}

function SeraFaq() {
  return (
    <div className="sera-world min-h-svh overflow-hidden bg-[#f6e8d8] text-[#5d2d26]">
      <SeraHeader active="faq" />
      <section className="relative isolate overflow-hidden px-6 py-16 sm:px-10 lg:px-14 lg:py-24"><SeraProofingField className="absolute -right-[18rem] -top-24 z-0 h-[46rem] w-[54rem] opacity-35" /><div className="relative z-10 mx-auto grid max-w-[92rem] gap-14 lg:grid-cols-[0.42fr_0.58fr]"><div><p className="font-serif text-3xl italic text-[#ff765f]">Before breakfast.</p><h1 className="mt-4 text-[clamp(4.8rem,9vw,8.5rem)] font-semibold leading-[0.74] tracking-[-0.09em]">Good<br />to know.</h1><Link href="/demos/sera/contact" className="mt-10 inline-flex items-center gap-3 bg-[#ff765f] px-5 py-3 text-sm font-semibold text-white shadow-[0_20px_60px_rgba(93,45,38,.18)]">Order inquiry <ArrowRight className="size-4" /></Link></div><div className="sera-depth-card bg-[#fff6ec]/92 p-6 backdrop-blur-md sm:p-9"><FaqList items={seraFaqs} itemClassName="border-[#5d2d26]/16" answerClassName="text-[#5d2d26]/60" /></div></div></section>
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
