const demos = [
  {
    id: "moss-mortar",
    number: "01",
    name: "Moss & Mortar",
    category: "Landscape studio",
    location: "Sacramento, CA",
    headline: "Outside, considered.",
    description: "An editorial, quietly premium direction for a landscape practice that treats a garden like architecture.",
    background: "#d8ddce",
    surface: "#eef0e7",
    ink: "#263329",
    accent: "#d7ff3f",
    shadow: "#a5ad9c",
  },
  {
    id: "northline",
    number: "02",
    name: "Northline",
    category: "Family dentistry",
    location: "Oakland, CA",
    headline: "Care, without the rush.",
    description: "A calm, lucid healthcare identity that replaces clinical coldness with rhythm, warmth, and direct language.",
    background: "#cbdcf2",
    surface: "#f2f6fb",
    ink: "#173a5a",
    accent: "#ff725e",
    shadow: "#9ebbd9",
  },
  {
    id: "sera",
    number: "03",
    name: "Sera",
    category: "Neighborhood bakery",
    location: "Long Beach, CA",
    headline: "Fresh by seven.",
    description: "A tactile, type-led system for a bakery with a tiny menu, a loyal neighborhood, and nothing to hide.",
    background: "#f0cdb3",
    surface: "#fff6ed",
    ink: "#6a2f25",
    accent: "#3155ff",
    shadow: "#d29e7e",
  },
];

type Demo = (typeof demos)[number];

function MossCanvas({ demo }: { demo: Demo }) {
  return (
    <div className="flex h-full flex-col" style={{ color: demo.ink }}>
      <div className="flex items-center justify-between border-b pb-4" style={{ borderColor: `${demo.ink}30` }}>
        <p className="text-sm font-semibold">Moss &amp; Mortar</p>
        <div className="flex gap-4 font-mono text-[8px] uppercase tracking-[0.12em]"><span>Work</span><span>Studio</span><span>Contact</span></div>
      </div>
      <div className="grid flex-1 grid-cols-[1fr_0.34fr] gap-6 py-8 sm:py-10">
        <div className="flex flex-col justify-between">
          <p className="font-mono text-[8px] uppercase tracking-[0.16em] opacity-55">Landscape design / Northern California</p>
          <p className="text-[2.65rem] font-semibold leading-[0.88] tracking-[-0.07em] sm:text-[4.6rem]">Outside,<span className="block font-serif font-normal italic">considered.</span></p>
          <p className="max-w-xs text-[10px] leading-5 opacity-60">Gardens and outdoor rooms made for how Northern California actually lives.</p>
        </div>
        <div className="relative border-l" style={{ borderColor: `${demo.ink}30` }}>
          <div className="concept-float absolute inset-x-3 top-0 aspect-square" style={{ background: demo.ink, boxShadow: `7px 7px 0 ${demo.shadow}` }} />
          <p className="absolute bottom-0 left-3 font-mono text-[8px] uppercase leading-4 tracking-[0.12em] opacity-55">Field notes<br />Season 26</p>
        </div>
      </div>
    </div>
  );
}

function NorthlineCanvas({ demo }: { demo: Demo }) {
  return (
    <div className="flex h-full flex-col" style={{ color: demo.ink }}>
      <div className="flex items-center justify-between font-mono text-[8px] uppercase tracking-[0.14em]"><span>Northline dental</span><span>Accepting new patients</span></div>
      <div className="grid flex-1 items-center gap-8 py-8 sm:grid-cols-[1.1fr_0.9fr] sm:py-10">
        <div>
          <p className="text-[2.7rem] font-semibold leading-[0.9] tracking-[-0.07em] sm:text-[4.5rem]">Care, without<span className="block font-serif font-normal italic">the rush.</span></p>
          <p className="mt-6 max-w-xs text-[10px] leading-5 opacity-60">A neighborhood practice built around time, clarity, and a genuinely calmer visit.</p>
        </div>
        <div className="relative min-h-56 border p-4" style={{ borderColor: `${demo.ink}30`, boxShadow: `9px 9px 0 ${demo.shadow}` }}>
          <p className="font-mono text-[8px] uppercase tracking-[0.14em] opacity-55">Next available</p>
          <p className="mt-5 text-5xl font-semibold tracking-[-0.07em]">Tue 14</p>
          <div className="absolute inset-x-4 bottom-4 flex items-center justify-between border-t pt-4 text-[9px] font-semibold" style={{ borderColor: `${demo.ink}30` }}><span>Book a visit</span><span className="concept-float grid size-8 place-items-center" style={{ background: demo.accent, color: "white" }}>↗</span></div>
        </div>
      </div>
      <div className="flex gap-5 border-t pt-4 font-mono text-[8px] uppercase tracking-[0.12em]" style={{ borderColor: `${demo.ink}30` }}><span>General</span><span>Cosmetic</span><span>Family</span></div>
    </div>
  );
}

function SeraCanvas({ demo }: { demo: Demo }) {
  return (
    <div className="flex h-full flex-col" style={{ color: demo.ink }}>
      <div className="flex items-center justify-between border-b pb-4" style={{ borderColor: `${demo.ink}30` }}><p className="font-serif text-2xl italic">Sera</p><p className="font-mono text-[8px] uppercase tracking-[0.14em]">Bakehouse / daily</p></div>
      <div className="grid flex-1 gap-6 py-7 sm:grid-cols-[1fr_0.42fr]">
        <div className="flex flex-col justify-between">
          <p className="text-[3rem] font-semibold leading-[0.86] tracking-[-0.075em] sm:text-[5.2rem]">Fresh by<span className="block font-serif font-normal italic">seven.</span></p>
          <div className="grid grid-cols-3 gap-2 font-mono text-[7px] uppercase tracking-[0.08em]"><span>Sourdough</span><span>Morning bun</span><span>Olive loaf</span></div>
        </div>
        <div className="relative overflow-hidden" style={{ background: demo.ink, boxShadow: `8px 8px 0 ${demo.shadow}` }}>
          <div className="demo-orbit absolute left-1/2 top-1/2 grid size-24 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border text-center font-serif text-xl italic" style={{ borderColor: demo.surface, color: demo.surface }}>Open<br />until sold</div>
        </div>
      </div>
      <div className="flex items-center justify-between border-t pt-4 text-[9px] font-semibold" style={{ borderColor: `${demo.ink}30` }}><span>207 Pine Avenue</span><span>Today / 7–2</span></div>
    </div>
  );
}

function ConceptCanvas({ demo, index }: { demo: Demo; index: number }) {
  return (
    <div className="project-card relative p-3 sm:p-5" style={{ background: demo.background }}>
      <div className="mb-3 flex justify-between font-mono text-[8px] uppercase tracking-[0.14em]" style={{ color: `${demo.ink}99` }}><span>Concept {demo.number}</span><span>Responsive study</span></div>
      <div className="project-frame relative min-h-[30rem] overflow-hidden border p-6 sm:min-h-[36rem] sm:p-8" style={{ background: demo.surface, borderColor: `${demo.ink}25`, boxShadow: `14px 14px 0 ${demo.shadow}` }}>
        {index === 0 ? <MossCanvas demo={demo} /> : index === 1 ? <NorthlineCanvas demo={demo} /> : <SeraCanvas demo={demo} />}
      </div>
      <div className="mt-4 flex justify-between font-mono text-[8px] uppercase tracking-[0.14em]" style={{ color: `${demo.ink}99` }}><span>Desktop / mobile</span><span>Hover the canvas</span></div>
    </div>
  );
}

export function DemoShowcase() {
  return (
    <section className="bg-navy text-white">
      <div className="overflow-hidden border-y border-white/15 py-4">
        <div className="marquee-track flex w-max gap-10 whitespace-nowrap font-mono text-[10px] uppercase tracking-[0.18em] text-white/55" aria-hidden="true">
          {Array.from({ length: 3 }).map((_, index) => (
            <span key={index}>Strategy / Art direction / Interface / Motion / Responsive / Development /</span>
          ))}
        </div>
      </div>

      <div className="site-container py-24 sm:py-32">
        <div className="space-y-28 sm:space-y-36">
          {demos.map((demo, index) => (
            <article id={demo.id} key={demo.name} className="grid gap-10 lg:grid-cols-[0.36fr_0.64fr] lg:gap-16" data-reveal>
              <div className="lg:sticky lg:top-28 lg:self-start">
                <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-mint">{demo.number} / {demo.category}</p>
                <h2 className="mt-6 text-4xl font-semibold tracking-[-0.06em] sm:text-5xl">{demo.name}</h2>
                <p className="mt-2 font-serif text-2xl italic text-white/55">{demo.headline}</p>
                <p className="mt-7 max-w-sm text-sm leading-7 text-white/55">{demo.description}</p>
                <div className="mt-9 border-y border-white/15 py-4 font-mono text-[9px] uppercase tracking-[0.12em] text-white/40">
                  <div className="flex justify-between"><span>Category</span><span>{demo.category}</span></div>
                  <div className="mt-3 flex justify-between"><span>Based in</span><span>{demo.location}</span></div>
                </div>
                <div className="mt-6 flex gap-2" aria-label={`${demo.name} color palette`}>
                  {[demo.background, demo.surface, demo.ink, demo.accent].map((color) => <span key={color} className="size-7 border border-white/15" style={{ background: color }} />)}
                </div>
              </div>
              <ConceptCanvas demo={demo} index={index} />
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
