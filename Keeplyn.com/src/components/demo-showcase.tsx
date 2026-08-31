const demos = [
  { name: "Moss & Mortar", line: "Outside, considered.", accent: "#c9ff3b", index: "01" },
  { name: "Northline", line: "Care, without the rush.", accent: "#7568ff", index: "02" },
  { name: "Sera", line: "Fresh by seven.", accent: "#ff765f", index: "03" },
];

function DemoVisual({ index, accent }: { index: number; accent: string }) {
  if (index === 0) {
    return (
      <div className="relative h-full overflow-hidden bg-[#0b0d0a]">
        <div className="absolute inset-0 opacity-25 [background-image:linear-gradient(rgba(255,255,255,.16)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.16)_1px,transparent_1px)] [background-size:64px_64px]" />
        <div className="absolute -right-[12%] top-1/2 aspect-square w-[65%] -translate-y-1/2 rounded-full border" style={{ borderColor: accent, boxShadow: `0 0 100px ${accent}2e` }} />
        <div className="absolute right-[5%] top-1/2 aspect-square w-[30%] -translate-y-1/2 rounded-full" style={{ background: accent }} />
        <p className="absolute bottom-8 left-8 text-[clamp(4rem,12vw,11rem)] font-semibold leading-[0.72] tracking-[-0.1em] text-white">MOSS</p>
      </div>
    );
  }

  if (index === 1) {
    return (
      <div className="relative h-full overflow-hidden bg-[#090812]">
        {[0, 1, 2].map((ring) => (
          <div
            key={ring}
            className="demo-orbit absolute left-1/2 top-1/2 aspect-square -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/15"
            style={{ width: `${34 + ring * 22}%`, animationDelay: `${ring * -1.8}s` }}
          />
        ))}
        <div className="concept-float absolute left-1/2 top-1/2 size-32 -translate-x-1/2 -translate-y-1/2 rounded-full" style={{ background: accent, boxShadow: `0 0 90px ${accent}` }} />
        <p className="absolute inset-x-0 bottom-8 text-center text-[clamp(4rem,12vw,11rem)] font-semibold leading-[0.72] tracking-[-0.1em] text-white">CARE</p>
      </div>
    );
  }

  return (
    <div className="relative h-full overflow-hidden bg-[#120a08]">
      <div className="absolute left-1/2 top-1/2 aspect-square w-[78%] -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/15" />
      <div className="absolute left-1/2 top-1/2 aspect-square w-[48%] -translate-x-1/2 -translate-y-1/2 rounded-full border-[3rem] border-white/8" />
      <div className="concept-float absolute left-1/2 top-1/2 aspect-square w-[21%] -translate-x-1/2 -translate-y-1/2 rounded-full" style={{ background: accent, boxShadow: `0 0 100px ${accent}66` }} />
      <p className="absolute bottom-8 left-8 font-serif text-[clamp(4rem,12vw,11rem)] italic leading-[0.72] tracking-[-0.08em] text-white">Sera</p>
    </div>
  );
}

export function DemoShowcase() {
  return (
    <section className="bg-[#050505] text-white">
      <div className="site-container space-y-24 pb-24 sm:space-y-32 sm:pb-32">
        {demos.map((demo, index) => (
          <article key={demo.name} className="grid min-h-[85svh] gap-8 border-t border-white/12 pt-8 lg:grid-cols-[0.28fr_0.72fr]">
            <div className="flex flex-col justify-between lg:py-3">
              <span className="text-[10px] tracking-[0.18em] text-white/32">{demo.index}</span>
              <div>
                <h2 className="text-4xl font-semibold tracking-[-0.06em] sm:text-5xl">{demo.name}</h2>
                <p className="mt-3 text-base text-white/45">{demo.line}</p>
              </div>
            </div>
            <div className="min-h-[34rem] overflow-hidden border border-white/12 bg-[#0b0b0f] shadow-[0_30px_100px_rgba(0,0,0,.55)]">
              <DemoVisual index={index} accent={demo.accent} />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
