import Link from "next/link";
import { ArrowDown, ArrowUpRight, Asterisk, Plus } from "lucide-react";
import { dailyBake, businessHref, type BusinessTemplate } from "./catalog";
import { Photo, TemplateButton } from "./template-chrome";

export function LandscapeTemplate({
  business: b,
}: {
  business: BusinessTemplate;
}) {
  return (
    <>
      <section className="moss-hero">
        <Photo image={b.hero} eager sizes="100vw" />
        <div className="moss-hero-shade" />
        <div className="moss-hero-copy">
          <p className="template-eyebrow">{b.eyebrow}</p>
          <h1>
            {b.headline[0]}
            <br />
            <em>{b.headline[1]}</em>
          </h1>
        </div>
        <div className="moss-hero-bottom">
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
        <span className="template-eyebrow">Rooted in place</span>
        <div>
          <h2>
            Less interruption.
            <br />
            <em>More belonging.</em>
          </h2>
          <div className="moss-intro-bottom">
            <p>{b.intro}</p>
            <Link
              href={businessHref(b, "about")}
              className="template-text-link"
            >
              Meet the studio <ArrowUpRight size={18} aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>
      <section className="moss-projects template-pad" id="gardens">
        <div className="template-section-label">
          <span>Selected gardens</span>
          <span>01—02 / California</span>
        </div>
        <div className="moss-project-grid">
          <Link href={businessHref(b, "about")} className="moss-project">
            <Photo image={b.detail} />
            <div>
              <h3>The quiet courtyard</h3>
              <span>Sacramento · Residential</span>
              <ArrowUpRight size={20} aria-hidden="true" />
            </div>
          </Link>
          <Link href={businessHref(b, "about")} className="moss-project">
            <Photo image={b.hero} />
            <div>
              <h3>A place to linger</h3>
              <span>Bay Area · Garden retreat</span>
              <ArrowUpRight size={20} aria-hidden="true" />
            </div>
          </Link>
        </div>
      </section>
      <section className="moss-services template-pad">
        <p className="template-eyebrow">From first sketch to first bloom</p>
        <div className="moss-service-list">
          {b.packages.map((p, i) => (
            <Link href={businessHref(b, "pricing")} key={p.name}>
              <span>0{i + 1}</span>
              <h3>{p.name}</h3>
              <ArrowUpRight aria-hidden="true" />
            </Link>
          ))}
        </div>
      </section>
      <section className="moss-closing-image">
        <Photo image={b.detail} sizes="100vw" />
        <div>
          <span className="template-eyebrow">Something to come home to</span>
          <p>
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

export function CareTemplate({ business: b }: { business: BusinessTemplate }) {
  return (
    <>
      <section className="northline-hero">
        <div className="northline-hero-copy">
          <span className="northline-status">
            <span />
            New faces welcome
          </span>
          <div>
            <p className="template-eyebrow">{b.eyebrow}</p>
            <h1>
              {b.headline[0]}
              <br />
              <span>{b.headline[1]}</span>
            </h1>
            <p className="northline-hero-description">{b.intro}</p>
            <TemplateButton business={b} />
          </div>
          <div className="northline-hero-meta">
            <Plus size={20} aria-hidden="true" />
            <span>
              Great care.
              <br />
              Right here in Oakland.
            </span>
            <span>
              YOU CAN
              <br />
              EXHALE NOW.
            </span>
          </div>
        </div>
        <div className="northline-portrait">
          <Photo image={b.hero} eager />
          <div className="northline-smile-sticker">
            <svg viewBox="0 0 100 70" aria-hidden="true">
              <path d="M10 15 Q50 92 90 15" />
            </svg>
            <span>Feel like yourself.</span>
          </div>
          <span className="northline-portrait-label">
            A GOOD REASON TO SMILE
          </span>
        </div>
      </section>
      <div className="northline-care-strip">
        <span>
          <Plus aria-hidden="true" />
          Whole-person care
        </span>
        <span>Clear costs</span>
        <span>Your pace, always</span>
        <span>A little less dental</span>
      </div>
      <section className="northline-approach template-pad">
        <div>
          <p className="template-eyebrow">Dentistry, with a human side</p>
          <h2>
            A better kind
            <br />
            of <span>open wide.</span>
          </h2>
        </div>
        <div>
          <p>
            No lectures. No mysteries. Just thoughtful care in a space that
            feels good to be in.
          </p>
          <Link href={businessHref(b, "about")} className="template-text-link">
            Get to know us <ArrowUpRight size={18} aria-hidden="true" />
          </Link>
        </div>
      </section>
      <section className="northline-space">
        <Photo image={b.detail} sizes="100vw" />
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
          {[
            ["01", "Keep it healthy.", "Prevention & cleanings", "prevent"],
            ["02", "Bring it back.", "Restorative dentistry", "restore"],
            ["03", "Make it yours.", "Cosmetic care", "smile"],
          ].map(([n, name, label, icon]) => (
            <Link href={businessHref(b, "pricing")} key={n}>
              <span>{n} /</span>
              <div
                className={`northline-care-symbol symbol-${icon}`}
                aria-hidden="true"
              >
                {icon === "restore" ? (
                  <Plus />
                ) : icon === "prevent" ? (
                  <Asterisk />
                ) : (
                  <svg viewBox="0 0 100 80">
                    <path d="M10 20 Q50 98 90 20" />
                  </svg>
                )}
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
          <strong>
            90<span>min</span>
          </strong>
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
  return (
    <>
      <div className="sera-announcement">
        <span>Made slowly. Gone quickly.</span>
        <Asterisk size={15} aria-hidden="true" />
        <span>{b.hours}</span>
      </div>
      <section className="sera-hero">
        <div className="sera-hero-title">
          <p className="template-eyebrow">{b.eyebrow}</p>
          <h1>
            {b.headline[0]} <em>{b.headline[1]}</em>
          </h1>
        </div>
        <div className="sera-hero-photo">
          <Photo image={b.hero} eager sizes="100vw" />
          <a href="#daily-bake" className="sera-sticker">
            <span>
              ALWAYS
              <br />
              FROM SCRATCH
            </span>
            <Asterisk size={38} aria-hidden="true" />
            <span>NEVER BORING</span>
          </a>
          <div className="sera-hero-caption">
            <p>{b.intro}</p>
            <TemplateButton business={b} page="pricing" light>
              Meet the morning menu
            </TemplateButton>
          </div>
        </div>
      </section>
      <div className="sera-ribbon" aria-hidden="true">
        <span>GOOD THINGS RISE</span>
        <Asterisk />
        <span>PASS THE BUTTER</span>
        <Asterisk />
        <span>GOOD THINGS RISE</span>
        <Asterisk />
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
        </div>
        <div className="sera-menu-list">
          {dailyBake.map((item, i) => (
            <Link key={item.name} href={businessHref(b, "pricing")}>
              <span className="sera-menu-number">0{i + 1}</span>
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
        <Photo image={b.detail} />
        <div>
          <span className="template-eyebrow">
            Your neighborhood morning ritual
          </span>
          <Asterisk className="sera-story-star" aria-hidden="true" />
          <h2>
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
        </div>
        <div>
          <p>{b.address}</p>
          <p>{b.hours}</p>
          <TemplateButton business={b} page="contact">
            Come say hello
          </TemplateButton>
        </div>
      </section>
    </>
  );
}
