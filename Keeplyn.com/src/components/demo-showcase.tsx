import { SectionHeading } from "./section-heading";

const demos = [
  {
    name: "Moss & Mortar",
    category: "Landscape Design",
    palette: "bg-[#dbe5d7]",
    accent: "bg-[#29382b]",
    text: "Outdoor spaces, thoughtfully grown.",
    tag: "Local service",
  },
  {
    name: "Northline",
    category: "Family Dentistry",
    palette: "bg-[#dcebf3]",
    accent: "bg-[#204e65]",
    text: "A calmer kind of dental care.",
    tag: "Healthcare",
  },
  {
    name: "Sera",
    category: "Neighborhood Bakehouse",
    palette: "bg-[#f2dfd0]",
    accent: "bg-[#7b3f2f]",
    text: "Made slowly. Enjoyed daily.",
    tag: "Hospitality",
  },
];

export function DemoShowcase() {
  return (
    <section id="work" className="section-space overflow-hidden bg-navy text-white">
      <div className="site-container">
        <div className="flex flex-col justify-between gap-8 lg:flex-row lg:items-end">
          <SectionHeading
            eyebrow="Concept work"
            title="Designed for the business you actually run."
            description="No cookie-cutter industry themes. Every Keeplyn site starts with your offer, your customers, and the action you want them to take."
            inverse
          />
          <p className="max-w-sm text-sm leading-6 text-white/45">
            These are tasteful concept businesses created to demonstrate Keeplyn&apos;s design range—never presented as real clients.
          </p>
        </div>

        <div className="mt-12 grid gap-5 lg:grid-cols-3">
          {demos.map((demo, index) => (
            <article
              key={demo.name}
              className={`overflow-hidden rounded-[1.75rem] ${
                index === 0 ? "lg:translate-y-6" : index === 2 ? "lg:translate-y-12" : ""
              }`}
            >
              <div className={`${demo.palette} relative aspect-[4/3] overflow-hidden p-4 text-navy`}>
                <div className="absolute -right-10 -top-14 size-44 rounded-full bg-white/35 blur-xl" />
                <div className="relative flex h-full flex-col overflow-hidden rounded-2xl border border-black/10 bg-white/75 shadow-xl shadow-navy/10 backdrop-blur">
                  <div className="flex h-11 items-center justify-between border-b border-black/8 px-4">
                    <div className="flex items-center gap-2">
                      <span className={`size-5 rounded-md ${demo.accent}`} />
                      <span className="text-[10px] font-bold tracking-tight">{demo.name}</span>
                    </div>
                    <div className="flex gap-2 text-[7px] font-semibold text-navy/55">
                      <span>Services</span>
                      <span>About</span>
                      <span>Contact</span>
                    </div>
                  </div>
                  <div className="grid flex-1 grid-cols-[1.2fr_0.8fr] gap-3 p-4">
                    <div className="flex flex-col justify-center">
                      <p className="mb-2 text-[7px] font-bold uppercase tracking-[0.18em] text-navy/45">
                        {demo.category}
                      </p>
                      <p className="max-w-[12rem] text-lg font-bold leading-[1.05] tracking-[-0.05em] sm:text-xl">
                        {demo.text}
                      </p>
                      <span className={`mt-4 w-fit rounded-full px-3 py-1.5 text-[7px] font-bold text-white ${demo.accent}`}>
                        Explore services
                      </span>
                    </div>
                    <div className={`relative overflow-hidden rounded-xl ${demo.accent}`}>
                      <div className="absolute inset-3 rounded-full border border-white/20" />
                      <div className="absolute bottom-3 left-3 right-3 h-1/2 rounded-lg bg-white/14" />
                      <div className="absolute -right-3 -top-3 size-14 rounded-full bg-white/15" />
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between bg-white/6 px-5 py-5">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-white">{demo.name}</h3>
                    <span className="rounded-full bg-mint/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-mint">
                      Demo
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-white/45">{demo.tag}</p>
                </div>
                <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-white/35">
                  Concept preview
                </span>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
