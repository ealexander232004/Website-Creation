import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { demoSlugs, templates, demoHref } from "./templates/catalog";
import { Brand, Photo } from "./templates/template-chrome";
import { templateFonts } from "./templates/typography";
import "./templates/templates.css";

export function DemoShowcase() {
  return (
    <section className={`template-collection site-container ${templateFonts}`}>
      <div className="template-collection-heading">
        <div>
          <p className="template-eyebrow">The Keeplyn collection / 01—03</p>
          <h1>
            Different businesses.
            <br />
            Different by design.
          </h1>
        </div>
        <p>
          Three original concept websites. Explore the pages, try the details,
          find your direction.
        </p>
      </div>
      <div className="template-collection-grid">
        {demoSlugs.map((id, i) => {
          const b = templates[id];
          return (
            <Link
              key={id}
              href={demoHref(id)}
              className={`template-collection-card collection-${id}`}
            >
              <div className="template-collection-preview">
                <Photo
                  image={b.hero}
                  eager={i === 0}
                  sizes={id === "northline" ? "50vw" : "100vw"}
                />
                <div className="collection-wordmark">
                  <Brand business={b} />
                </div>
                <div className="collection-headline">
                  {b.headline[0]}
                  {id === "sera" ? " " : <br />}
                  <em className={id === "northline" ? "not-italic" : ""}>
                    {b.headline[1]}
                  </em>
                </div>
                <span className="collection-open">
                  <ArrowUpRight aria-hidden="true" />
                </span>
              </div>
              <div className="template-collection-caption">
                <div>
                  <h2>{b.name}</h2>
                  <p>
                    0{i + 1} / {b.category}
                  </p>
                </div>
                <span>
                  Explore website <ArrowUpRight size={17} aria-hidden="true" />
                </span>
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
