import Link from "next/link";
import type { CSSProperties } from "react";
import {
  ArrowDown,
  ArrowUpRight,
  Asterisk,
  CalendarDays,
  Plus,
} from "lucide-react";
import { dailyBake, businessHref, type BusinessTemplate } from "./catalog";
import { Photo, TemplateButton } from "./template-chrome";
import {
  Contours,
  Glyph,
  MENU_GLYPHS,
  Marquee,
  SpinBadge,
  Sprig,
  TemplateMap,
  TimeDial,
} from "./template-art";

const delay = (ms: number) => ({ "--d": `${ms}ms` }) as CSSProperties;

const nativePlants = [
  "Live oak",
  "Gulf muhly",
  "Texas sage",
  "Bluebonnet",
  "Mexican feathergrass",
  "Texas redbud",
  "Cedar sage",
  "Black-eyed Susan",
];

export function LandscapeTemplate({
  business: b,
}: {
  business: BusinessTemplate;
}) {
  const [water, passage = water] = b.gallery;
  const projects = [
    { image: b.detail, title: "The quiet courtyard", meta: "Austin · Residential" },
    { image: water, title: "A place to linger", meta: "Dripping Springs · Rain garden" },
    { image: passage, title: "Evening passage", meta: "San Antonio · Light & planting" },
  ];
  const serviceImages = [b.detail, water, b.hero];
  return (
    <>
      <section className="moss-hero">
        <Photo image={b.hero} eager sizes="100vw" className="t-kenburns" />
        <div className="moss-hero-shade" />
        <div className="moss-hero-copy">
          <p className="template-eyebrow t-enter">{b.eyebrow}</p>
          <h1 className="t-enter" style={delay(140)}>
            {b.headline[0]}
            <br />
            <em>{b.headline[1]}</em>
          </h1>
        </div>
        <div className="moss-hero-bottom t-enter" style={delay(420)}>
          <p>
            Landscape design
            <br />
            {b.location}
          </p>
          <a href="#gardens" className="moss-explore">
            Step outside{" "}
            <span className="template-circle">
              <ArrowDown size={20} aria-hidden="true" />
            </span>
          </a>
          <span className="moss-hero-index">01 / THE LIVING LANDSCAPE</span>
        </div>
      </section>
      <section className="moss-intro template-pad">
        <div className="moss-intro-aside">
          <span className="template-eyebrow">Rooted in place</span>
          <div className="moss-arch t-rise">
            <Photo
              image={passage}
              className="t-parallax"
              sizes="(min-width: 900px) 28vw, 70vw"
            />
          </div>
        </div>
        <div className="moss-intro-main">
          <Contours className="moss-intro-contours" />
          <Sprig className="moss-intro-sprig" />
          <h2 className="t-rise">
            Less interruption.
            <br />
            <em>More belonging.</em>
          </h2>
          <div className="moss-intro-bottom t-rise">
            <p>{b.intro}</p>
            <Link href={businessHref(b, "about")} className="template-text-link">
              Meet the studio <ArrowUpRight size={18} aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>
      <section className="moss-projects template-pad" id="gardens">
        <div className="template-section-label">
          <span>Selected gardens</span>
          <span>{b.location}</span>
        </div>
        <div className="moss-project-grid">
          {[projects.slice(0, 1), projects.slice(1)].map((column, c) => (
            <div key={c} className="moss-project-column">
              {column.map((p, i) => (
                <Link
                  key={p.title}
                  href={businessHref(b, "about")}
                  className="moss-project t-rise"
                >
                  <Photo
                    image={p.image}
                    className="t-parallax"
                    sizes={c === 0 ? "(min-width: 900px) 52vw, 100vw" : "(min-width: 900px) 40vw, 100vw"}
                  />
                  <div>
                    <span className="moss-project-index">0{c + i + 1}</span>
                    <h3>{p.title}</h3>
                    <span>{p.meta}</span>
                    <ArrowUpRight size={20} aria-hidden="true" />
                  </div>
                </Link>
              ))}
              {c === 0 && (
                <div className="moss-project-note t-rise">
                  <Sprig />
                  <p>
                    Native planting.
                    <br />
                    <em>Four good seasons.</em>
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
      <Marquee className="moss-species" decorative>
        {nativePlants.map((plant) => (
          <span key={plant}>
            <em>{plant}</em>
            <Glyph kind="seedling" />
          </span>
        ))}
      </Marquee>
      <section className="moss-services template-pad">
        <div className="moss-services-aside">
          <p className="template-eyebrow">From first sketch to first bloom</p>
          <div className="moss-services-glyphs" aria-hidden="true">
            <Glyph kind="seedling" />
            <Glyph kind="garden" />
            <Glyph kind="landscape" />
          </div>
        </div>
        <div className="moss-service-list">
          {b.packages.map((p, i) => (
            <Link href={businessHref(b, "pricing")} key={p.name} className="t-rise">
              <span>0{i + 1}</span>
              <h3>{p.name}</h3>
              <span className="moss-service-price">{p.price}</span>
              <span className="moss-service-thumb" aria-hidden="true">
                <Photo image={serviceImages[i]} sizes="260px" />
              </span>
              <ArrowUpRight aria-hidden="true" />
            </Link>
          ))}
        </div>
      </section>
      <section className="moss-closing-image">
        <Photo image={water} sizes="100vw" className="t-parallax" />
        <div>
          <span className="template-eyebrow">Something to come home to</span>
          <p className="t-rise">
            Let life
            <br />
            <em>grow around you.</em>
          </p>
          <TemplateButton business={b} light />
        </div>
      </section>
    </>
  );
}

const careNotes = [
  "Whole-person care",
  "Clear costs",
  "Your pace, always",
  "A little less dental",
  "Same-day spaces",
];

export function CareTemplate({ business: b }: { business: BusinessTemplate }) {
  const [consult] = b.gallery;
  return (
    <>
      <section className="northline-hero">
        <div className="northline-hero-copy">
          <Glyph kind="plus" className="northline-hero-plus" />
          <span className="northline-status">
            <span />
            New faces welcome
          </span>
          <div>
            <p className="template-eyebrow t-enter">{b.eyebrow}</p>
            <h1 className="t-enter" style={delay(120)}>
              {b.headline[0]}
              <br />
              <span>{b.headline[1]}</span>
            </h1>
            <p className="northline-hero-description t-enter" style={delay(260)}>
              {b.intro}
            </p>
            <div className="t-enter" style={delay(360)}>
              <TemplateButton business={b} />
            </div>
          </div>
          <div className="northline-hero-meta">
            <Plus size={20} aria-hidden="true" />
            <span>
              Great care.
              <br />
              Right here in {b.location.split(",")[0]}.
            </span>
            <span>
              YOU CAN
              <br />
              EXHALE NOW.
            </span>
          </div>
        </div>
        <div className="northline-portrait">
          <Photo image={b.hero} eager className="t-kenburns" />
          <div className="northline-appointment t-enter" style={delay(520)}>
            <span className="northline-appointment-icon">
              <CalendarDays size={20} aria-hidden="true" />
            </span>
            <span>
              <small>Next opening</small>
              <strong>Tue · 9:30 AM</strong>
            </span>
            <span className="northline-appointment-live" aria-hidden="true" />
          </div>
          <div className="northline-smile-sticker">
            <svg viewBox="0 0 100 70" aria-hidden="true">
              <path d="M10 15 Q50 92 90 15" pathLength="1" />
            </svg>
            <span>Feel like yourself.</span>
          </div>
          <span className="northline-portrait-label">
            A GOOD REASON TO SMILE
          </span>
        </div>
      </section>
      <Marquee className="northline-care-strip">
        {careNotes.map((note) => (
          <span key={note}>
            <Asterisk aria-hidden="true" />
            {note}
          </span>
        ))}
      </Marquee>
      <section className="northline-approach template-pad">
        <div>
          <p className="template-eyebrow">Dentistry, with a human side</p>
          <h2 className="t-rise">
            A better kind
            <br />
            of <span>open wide.</span>
          </h2>
          <p>
            No lectures. No mysteries. Just thoughtful care in a space that
            feels good to be in.
          </p>
          <Link href={businessHref(b, "about")} className="template-text-link">
            Get to know us <ArrowUpRight size={18} aria-hidden="true" />
          </Link>
        </div>
        <div className="northline-approach-visual t-rise">
          <Photo
            image={consult}
            className="t-parallax"
            sizes="(min-width: 900px) 45vw, 100vw"
          />
          <span className="northline-bubble">Every question welcome</span>
          <span className="northline-approach-smile" aria-hidden="true">
            <Glyph kind="smile" />
          </span>
        </div>
      </section>
      <section className="northline-space t-unveil">
        <Photo image={b.detail} sizes="100vw" className="t-parallax" />
        <div className="northline-space-note">
          <span className="template-eyebrow">Come on in</span>
          <p>
            Room to
            <br />
            feel at ease.
          </p>
          <Link
            href={businessHref(b, "contact")}
            className="template-circle"
            aria-label="Visit Northline"
          >
            <ArrowUpRight aria-hidden="true" />
          </Link>
        </div>
      </section>
      <section className="northline-services template-pad">
        <div className="template-section-label">
          <span>Care for every chapter</span>
          <Link href={businessHref(b, "pricing")}>
            See care &amp; costs <ArrowUpRight size={16} aria-hidden="true" />
          </Link>
        </div>
        <div className="northline-service-grid">
          {(
            [
              ["01", "Keep it healthy.", "Prevention & cleanings", "asterisk"],
              ["02", "Bring it back.", "Restorative dentistry", "plus"],
              ["03", "Make it yours.", "Cosmetic care", "smile"],
            ] as const
          ).map(([n, name, label, icon]) => (
            <Link href={businessHref(b, "pricing")} key={n} className="t-rise">
              <span>{n} /</span>
              <div className={`northline-care-symbol symbol-${icon}`}>
                <Glyph kind={icon} />
              </div>
              <h3>{name}</h3>
              <p>
                {label}
                <ArrowUpRight size={19} aria-hidden="true" />
              </p>
            </Link>
          ))}
        </div>
      </section>
      <section className="northline-first-visit template-pad">
        <div>
          <p className="template-eyebrow">Your first visit</p>
          <h2>
            Time for
            <br />
            <span>all your questions.</span>
          </h2>
          <TemplateButton business={b} light />
        </div>
        <div className="northline-time">
          <div className="northline-dial">
            <TimeDial minutes={90} />
            <strong>
              90<span>min</span>
            </strong>
          </div>
          <p>
            A conversation. An exam.
            <br />A clear plan, made together.
          </p>
        </div>
      </section>
    </>
  );
}

export function BakeryTemplate({
  business: b,
}: {
  business: BusinessTemplate;
}) {
  const [loaves] = b.gallery;
  return (
    <>
      <div className="sera-announcement">
        <span>Made slowly. Gone quickly.</span>
        <Asterisk size={15} aria-hidden="true" />
        <span>{b.hours}</span>
      </div>
      <section className="sera-hero">
        <div className="sera-hero-title">
          <p className="template-eyebrow t-enter">{b.eyebrow}</p>
          <h1 className="t-enter" style={delay(120)}>
            {b.headline[0]} <em>{b.headline[1]}</em>
          </h1>
        </div>
        <div className="sera-hero-photo">
          <Photo image={b.hero} eager sizes="100vw" className="t-kenburns" />
          <a
            href="#daily-bake"
            className="sera-sticker"
            aria-label="Always from scratch, never boring. See the daily bake."
          >
            <SpinBadge
              id="sera-hero-badge"
              text="ALWAYS FROM SCRATCH • NEVER BORING • "
            >
              <Asterisk size={38} aria-hidden="true" />
            </SpinBadge>
          </a>
          <div className="sera-hero-caption">
            <p>{b.intro}</p>
            <TemplateButton business={b} page="pricing" light>
              Meet the morning menu
            </TemplateButton>
          </div>
        </div>
      </section>
      <div className="sera-ribbons" aria-hidden="true">
        <Marquee className="sera-ribbon" decorative>
          {[
            "Good things rise",
            "Pass the butter",
            "Baked before sunrise",
            "Crumbs welcome",
            "Still warm",
            "Worth the early alarm",
            "Slow dough, good mornings",
          ].map((t) => (
            <span key={t}>
              {t}
              <Asterisk />
            </span>
          ))}
        </Marquee>
      </div>
      <section className="sera-menu-section template-pad" id="daily-bake">
        <div className="sera-menu-heading">
          <span className="template-eyebrow">Fresh out of the oven</span>
          <h2>
            The usual
            <br />
            <em>temptations.</em>
          </h2>
          <p>
            A short menu. A long fermentation.
            <br />
            Baked fresh until we sell out.
          </p>
          <Link
            href={businessHref(b, "pricing")}
            className="template-text-link"
          >
            The full menu <ArrowUpRight size={20} aria-hidden="true" />
          </Link>
          <figure className="sera-polaroid t-rise">
            <Photo image={loaves} sizes="(min-width: 900px) 30vw, 80vw" />
            <figcaption>Out of the oven, 6:40am</figcaption>
          </figure>
        </div>
        <div className="sera-menu-list">
          {dailyBake.map((item, i) => (
            <Link key={item.name} href={businessHref(b, "pricing")} className="t-rise">
              <span className="sera-menu-icon">
                <Glyph kind={MENU_GLYPHS[i % MENU_GLYPHS.length]} />
              </span>
              <div>
                <h3>{item.name}</h3>
                <p>{item.note}</p>
              </div>
              <span className="sera-menu-price">{item.price}</span>
            </Link>
          ))}
          <span className="sera-menu-footnote">
            Best enjoyed with absolutely no plans.
          </span>
        </div>
      </section>
      <section className="sera-table-story">
        <Photo image={b.detail} className="t-parallax" />
        <div>
          <span className="template-eyebrow">
            Your neighborhood morning ritual
          </span>
          <Asterisk className="sera-story-star" aria-hidden="true" />
          <h2 className="t-rise">
            Made to
            <br />
            <em>be shared.</em>
          </h2>
          <p>
            A loaf under your arm. Coffee with a friend. We make the little
            things that make a day.
          </p>
          <TemplateButton business={b} page="about">
            A little about us
          </TemplateButton>
        </div>
      </section>
      <section className="sera-visit template-pad">
        <div>
          <span className="template-eyebrow">Follow your nose</span>
          <h2>
            Same corner.
            <br />
            <em>Fresh every day.</em>
          </h2>
          <div className="sera-visit-details">
            <p>{b.address}</p>
            <p>{b.hours}</p>
            <TemplateButton business={b} page="contact">
              Come say hello
            </TemplateButton>
          </div>
        </div>
        <div className="sera-visit-map t-rise">
          <TemplateMap id="sera" />
        </div>
      </section>
    </>
  );
}
