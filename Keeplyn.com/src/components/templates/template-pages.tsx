import Link from "next/link";
import { ArrowUpRight, Plus } from "lucide-react";
import {
  dailyBake,
  businessHref,
  templates,
  type BusinessTemplate,
  type DemoPage,
  type DemoSlug,
} from "./catalog";
import {
  Photo,
  TemplateButton,
  TemplateFooter,
  TemplateHeader,
} from "./template-chrome";
import {
  LandscapeTemplate,
  CareTemplate,
  BakeryTemplate,
} from "./template-homes";
import { TemplateForm } from "./template-form";

function About({ business: b }: { business: BusinessTemplate }) {
  return (
    <>
      <section className="template-about-hero">
        <div>
          <p className="template-eyebrow">
            {b.nav.about} / {b.location}
          </p>
          <h1>{b.about.title}</h1>
          <p>{b.about.text}</p>
          <TemplateButton business={b} />
        </div>
        <Photo image={b.detail} eager />
      </section>
      <section className="template-principles template-pad">
        <p className="template-eyebrow">A few things we believe</p>
        <div>
          {b.about.principles.map(([title, text], i) => (
            <article key={title}>
              <span>0{i + 1}</span>
              <h2>{title}</h2>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="template-about-image">
        <Photo image={b.hero} sizes="100vw" />
        <p>{b.intro}</p>
      </section>
    </>
  );
}

function Faq({ business: b }: { business: BusinessTemplate }) {
  return (
    <section className="template-faq template-pad">
      <div className="template-faq-intro">
        <p className="template-eyebrow">A little clarity</p>
        <h1>
          {b.id === "moss"
            ? "Before we dig in."
            : b.id === "sera"
              ? "Good questions. Fresh answers."
              : "Feel a little more ready."}
        </h1>
        <Photo image={b.detail} />
        <Link href={businessHref(b, "contact")} className="template-text-link">
          Ask us something else <ArrowUpRight size={18} aria-hidden="true" />
        </Link>
      </div>
      <div className="template-faq-list">
        {b.faqs.map((item, i) => (
          <details key={item.question}>
            <summary>
              <span>0{i + 1}</span>
              <h2>{item.question}</h2>
              <Plus size={21} aria-hidden="true" />
            </summary>
            <p>{item.answer}</p>
          </details>
        ))}
      </div>
    </section>
  );
}

function Pricing({ business: b }: { business: BusinessTemplate }) {
  return (
    <>
      <section className="template-price-hero">
        <div>
          <span className="template-eyebrow">{b.nav.pricing}</span>
          <h1>
            {b.id === "moss"
              ? "A plan for your patch."
              : b.id === "northline"
                ? "Good care. Clear costs."
                : "Your morning, made."}
          </h1>
          <p>
            {b.id === "sera"
              ? "A little something for you. A whole spread for your people."
              : "A clear starting point. A thoughtful way forward."}
          </p>
        </div>
        <Photo image={b.id === "sera" ? b.hero : b.detail} eager />
      </section>
      {b.id === "sera" && (
        <section className="template-daily-menu template-pad">
          <h2>The daily bake</h2>
          <div>
            {dailyBake.map((item) => (
              <article key={item.name}>
                <div>
                  <h3>{item.name}</h3>
                  <p>{item.note}</p>
                </div>
                <span>{item.price}</span>
              </article>
            ))}
          </div>
        </section>
      )}
      <section className="template-prices template-pad">
        <div className="template-section-label">
          <span>
            {b.id === "sera"
              ? "For a full table / Catering"
              : b.id === "moss"
                ? "Design services"
                : "Self-pay options"}
          </span>
          <span>01—03</span>
        </div>
        <div className="template-price-grid">
          {b.packages.map((p, i) => (
            <article key={p.name}>
              <span className="template-eyebrow">
                0{i + 1} /{" "}
                {b.id === "moss"
                  ? "Design"
                  : b.id === "sera"
                    ? "To share"
                    : "Care"}
              </span>
              <h2>{p.name}</h2>
              <p>{p.detail}</p>
              <strong>{p.price}</strong>
              <ul>
                {p.features.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
              <TemplateButton business={b}>
                {b.id === "moss"
                  ? "Talk about your garden"
                  : b.id === "sera"
                    ? "Plan an order"
                    : "Book a visit"}
              </TemplateButton>
            </article>
          ))}
        </div>
        <p className="template-pricing-note">{b.pricingNote}</p>
      </section>
    </>
  );
}

function Contact({
  business: b,
  booking,
}: {
  business: BusinessTemplate;
  booking: boolean;
}) {
  return (
    <section className="template-contact">
      <div className="template-contact-intro">
        <div>
          <p className="template-eyebrow">
            {booking ? b.action : b.nav.contact}
          </p>
          <h1>
            {booking && b.id !== "sera"
              ? b.id === "moss"
                ? "Every garden starts somewhere."
                : "Let’s get you settled in."
              : b.contactTitle}
          </h1>
          <p>{b.contactNote}</p>
        </div>
        <Photo image={b.detail} />
        <div className="template-contact-details">
          <p>{b.address}</p>
          <p>{b.hours}</p>
        </div>
      </div>
      <div className="template-contact-form">
        <span className="template-eyebrow">
          {booking ? "Make a little room" : "Drop us a note"}
        </span>
        <h2>
          {booking && b.id !== "sera" ? "Find your time." : "Hello, you."}
        </h2>
        <TemplateForm business={b} booking={booking} />
      </div>
    </section>
  );
}

/** Each template has its own composition; the business record supplies its content. */
export function BusinessWebsite({
  business: b,
  page = "home",
}: {
  business: BusinessTemplate;
  page?: DemoPage;
}) {
  return (
    <div className={`business-template template-${b.id} template-page-${page}`}>
      <TemplateHeader business={b} active={page} />
      {page === "home" ? (
        b.id === "moss" ? (
          <LandscapeTemplate business={b} />
        ) : b.id === "northline" ? (
          <CareTemplate business={b} />
        ) : (
          <BakeryTemplate business={b} />
        )
      ) : page === "about" ? (
        <About business={b} />
      ) : page === "faq" ? (
        <Faq business={b} />
      ) : page === "pricing" ? (
        <Pricing business={b} />
      ) : (
        <Contact business={b} booking={page === "booking"} />
      )}
      <TemplateFooter business={b} />
    </div>
  );
}

export function DemoWebsite({
  demo,
  page = "home",
}: {
  demo: DemoSlug;
  page?: DemoPage;
}) {
  return <BusinessWebsite business={templates[demo]} page={page} />;
}
