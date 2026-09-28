export const demoSlugs = ["moss", "northline", "sera"] as const;
export type DemoSlug = (typeof demoSlugs)[number];
export const demoPages = [
  "home",
  "about",
  "faq",
  "pricing",
  "contact",
  "booking",
] as const;
export type DemoPage = (typeof demoPages)[number];
export function isDemoSlug(value: string): value is DemoSlug {
  return demoSlugs.includes(value as DemoSlug);
}
export function isDemoPage(value: string): value is DemoPage {
  return demoPages.includes(value as DemoPage);
}
export type FaqItem = { question: string; answer: string };
export type TemplateImage = { src: string; alt: string };
export type BusinessTemplate = {
  id: DemoSlug;
  basePath: string;
  wordmark?: [string, string];
  name: string;
  shortName: string;
  category: string;
  collection: string;
  location: string;
  address: string;
  hours: string;
  eyebrow: string;
  headline: [string, string, string?];
  intro: string;
  action: string;
  closing: string;
  hero: TemplateImage;
  detail: TemplateImage;
  /** Supporting photography used by the project, story, and about compositions. */
  gallery: [TemplateImage, ...TemplateImage[]];
  nav: { about: string; pricing: string; contact: string };
  about: { title: string; text: string; principles: [string, string][] };
  packages: {
    name: string;
    price: string;
    detail: string;
    features: string[];
  }[];
  faqs: FaqItem[];
  pricingNote: string;
  contactTitle: string;
  contactNote: string;
};

const mossPackages = [
  {
    name: "Planting plan",
    price: "$1,800",
    detail: "A focused planting direction for one established outdoor space.",
    features: [
      "Site walk and light study",
      "Custom plant palette",
      "Placement plan",
      "Care notes",
    ],
  },
  {
    name: "Garden design",
    price: "$4,800",
    detail:
      "A complete design for a courtyard, front garden, or compact backyard.",
    features: [
      "Concept and material plan",
      "Planting design",
      "Lighting direction",
      "Two design revisions",
    ],
  },
  {
    name: "Full landscape",
    price: "$12k+",
    detail:
      "A ground-up landscape system carried from first sketch through installation.",
    features: [
      "Full property master plan",
      "Builder-ready documents",
      "Sourcing and contractor support",
      "First-year garden review",
    ],
  },
];

const northlinePrices = [
  {
    name: "New patient visit",
    price: "$195",
    detail:
      "A generous first appointment with imaging, exam, and a written care plan.",
    features: [
      "90-minute appointment",
      "Digital imaging",
      "Comprehensive exam",
      "Plain-language treatment plan",
    ],
  },
  {
    name: "Preventive visit",
    price: "$165",
    detail: "Routine cleaning and prevention, paced around your comfort.",
    features: [
      "Professional cleaning",
      "Gum health screening",
      "Oral cancer screening",
      "Personal home-care guidance",
    ],
  },
  {
    name: "Northline plan",
    price: "$39/mo",
    detail: "Simple preventive care for patients without dental insurance.",
    features: [
      "Two preventive visits",
      "Annual imaging",
      "Emergency exam",
      "15% off restorative care",
    ],
  },
];

const seraPackages = [
  {
    name: "Morning table",
    price: "$96",
    detail: "An easy pastry spread for eight early risers.",
    features: [
      "Eight mixed pastries",
      "One country loaf",
      "Seasonal jam",
      "Compostable serviceware",
    ],
  },
  {
    name: "Office spread",
    price: "$180",
    detail: "Breakfast for a team of fifteen, packed and ready to share.",
    features: [
      "Fifteen mixed pastries",
      "Two savory focaccias",
      "Batch-brew coffee",
      "Local delivery",
    ],
  },
  {
    name: "Celebration bake",
    price: "$260",
    detail: "A generous, custom assortment for gatherings up to twenty-four.",
    features: [
      "Seasonal pastry centerpiece",
      "Two bread selections",
      "Sweet and savory mix",
      "Custom menu card",
    ],
  },
];

const mossFaqs: FaqItem[] = [
  {
    question: "What kinds of spaces do you design?",
    answer:
      "Courtyards, front gardens, backyards, and full residential landscapes across Central Texas and the Hill Country.",
  },
  {
    question: "Can you work with an existing garden?",
    answer:
      "Yes. We keep what is thriving, edit what is not, and design the next layer around mature plants and real site conditions.",
  },
  {
    question: "How long does design take?",
    answer:
      "A focused planting plan takes about four weeks. Full landscapes typically take eight to twelve weeks before construction.",
  },
  {
    question: "Do you manage installation?",
    answer:
      "We can source plants, coordinate trusted installers, review the work, and return for a first-season garden check.",
  },
  {
    question: "Where does a project begin?",
    answer:
      "With a short consultation, a few site photos, and an honest conversation about budget, timing, and how you want to live outside.",
  },
];

const northlineFaqs: FaqItem[] = [
  {
    question: "Do you accept insurance?",
    answer:
      "We work with major PPO plans, check benefits before treatment, and show insurance and self-pay costs up front.",
  },
  {
    question: "What happens at a first visit?",
    answer:
      "A conversation, comfortable digital imaging, a comprehensive exam, and a clear written plan. We reserve ninety unhurried minutes.",
  },
  {
    question: "Can you help with dental anxiety?",
    answer:
      "Absolutely. Tell us what has felt difficult before. We agree on pause signals, explain each step, and move at your pace.",
  },
  {
    question: "Do you see children?",
    answer:
      "Yes. Northline welcomes families and adapts visits for young patients, sensory needs, and first-ever appointments.",
  },
  {
    question: "What if I have an urgent problem?",
    answer:
      "Call early. Same-day spaces are held Monday through Thursday, with after-hours triage for existing patients.",
  },
];

const seraFaqs: FaqItem[] = [
  {
    question: "Can I preorder the daily bake?",
    answer:
      "Country loaves and pastry boxes can be reserved forty-eight hours ahead. A small walk-in batch always stays on the shelf.",
  },
  {
    question: "What time do you sell out?",
    answer:
      "It changes with the day. Bread usually lasts through noon; laminated pastry tends to move fastest before nine.",
  },
  {
    question: "Do you accommodate allergies?",
    answer:
      "Our kitchen handles wheat, dairy, eggs, sesame, and nuts. We label every item, but cannot promise an allergen-free environment.",
  },
  {
    question: "Is local delivery available?",
    answer:
      "Yes for catering orders over $150 on the Portland peninsula. Smaller orders are ready for pickup from seven.",
  },
  {
    question: "Do you bake for wholesale partners?",
    answer:
      "A small number of restaurants receive bread Tuesday through Saturday. Send an inquiry with volume and timing.",
  },
];

// Content is separate from the three layouts. Copy a record to adapt a template.
export const templates: Record<DemoSlug, BusinessTemplate> = {
  moss: {
    id: "moss",
    basePath: "/demos/moss",
    wordmark: ["Moss", "& Mortar"],
    name: "Moss & Mortar",
    shortName: "Moss",
    category: "Landscape studio",
    collection: "The landscape collection",
    location: "Central Texas",
    address: "Austin · Dripping Springs · San Antonio",
    hours: "Monday–Friday · 9am–5pm",
    eyebrow: "Gardens for a slower life",
    headline: ["A little closer", "to the wild."],
    intro:
      "Considered landscapes. Native planting. Places that get better with time.",
    action: "Start a garden",
    closing: "Good things take root.",
    hero: {
      src: "/demos/templates/moss-hero.webp",
      alt: "An olive tree above a reflecting pool and limestone path in a lush courtyard",
    },
    detail: {
      src: "/demos/templates/moss-detail.webp",
      alt: "Sunlit native grasses and limestone steps around an olive tree",
    },
    gallery: [
      {
        src: "/demos/templates/moss-water.webp",
        alt: "Evening light on ornamental grasses beside a dry-stone wall and still water",
      },
      {
        src: "/demos/templates/moss-passage.webp",
        alt: "A softly lit stone passage lined with ferns, boxwood, and multi-stem trees",
      },
    ],
    nav: { about: "The studio", pricing: "Services", contact: "Get in touch" },
    about: {
      title: "A garden, not a grand gesture.",
      text: "We are a small landscape studio working with the grain of the Texas Hill Country. We listen to the land, keep what belongs, and make room for life outside.",
      principles: [
        [
          "Listen to the land",
          "Sun, soil, water. We start with what is already here.",
        ],
        [
          "Make less, mean more",
          "A restrained material palette. Room for the planting to lead.",
        ],
        [
          "Leave room for time",
          "A garden should be more interesting in five years.",
        ],
      ],
    },
    packages: mossPackages,
    faqs: mossFaqs,
    pricingNote:
      "Design fees only. Construction, permits, and installation are quoted separately. A 50% deposit reserves your project.",
    contactTitle: "Tell us about your patch of earth.",
    contactNote:
      "A few details about your space are all we need to begin. We usually reply within two working days.",
  },
  northline: {
    id: "northline",
    basePath: "/demos/northline",
    name: "Northline",
    shortName: "Northline",
    category: "Family dentistry",
    collection: "The care collection",
    location: "Chicago, Illinois",
    address: "2150 N Clark Street · Chicago, IL",
    hours: "Monday–Thursday · 8am–5pm",
    eyebrow: "A fresh take on dentistry",
    headline: ["Less nerves.", "More you."],
    intro:
      "Good dentistry starts with feeling good about being here. Come as you are. We will take it from there.",
    action: "Book your first visit",
    closing: "Your next chapter. With a smile.",
    hero: {
      src: "/demos/templates/northline-hero.webp",
      alt: "A woman with freckles smiling naturally in warm afternoon sunshine",
    },
    detail: {
      src: "/demos/templates/northline-space.webp",
      alt: "A bright dental suite with a cobalt tiled wall and soft natural light",
    },
    gallery: [
      {
        src: "/demos/templates/northline-consult.webp",
        alt: "A dentist and a relaxed patient talking in a bright treatment room",
      },
    ],
    nav: { about: "Our approach", pricing: "Care & costs", contact: "Find us" },
    about: {
      title: "People first. Teeth, too.",
      text: "A neighborhood dental studio built around a simple idea: you deserve to feel at ease. Longer appointments, clear answers, and a team that listens before it looks.",
      principles: [
        [
          "Time to talk",
          "Ninety minutes for your first visit. Every question is welcome.",
        ],
        ["Your pace", "Pause signals, quieter rooms, and each step explained."],
        [
          "The full picture",
          "A written care plan and costs before you decide.",
        ],
      ],
    },
    packages: northlinePrices,
    faqs: northlineFaqs,
    pricingNote:
      "Sample self-pay fees. Insurance benefits and treatment costs are reviewed before care begins.",
    contactTitle: "A friendly place to start.",
    contactNote:
      "Questions about your first visit or insurance? Leave a note for the team.",
  },
  sera: {
    id: "sera",
    basePath: "/demos/sera",
    name: "Sera",
    shortName: "Sera",
    category: "Neighborhood bakery",
    collection: "The neighborhood collection",
    location: "Portland, Maine",
    address: "88 Exchange Street · Portland, ME",
    hours: "Tuesday–Sunday · 7am–2pm",
    eyebrow: "Bread. Butter. Better mornings.",
    headline: ["Oh,", "crumbs."],
    intro: "Slow dough. Hot coffee. Something worth getting out of bed for.",
    action: "Order for the table",
    closing: "See you bright & early.",
    hero: {
      src: "/demos/templates/sera-hero.webp",
      alt: "Golden flaky croissants and espresso on a cherry-red cafe table",
    },
    detail: {
      src: "/demos/templates/sera-table.webp",
      alt: "Hands sharing sourdough with whipped butter, cherry jam, and coffee",
    },
    gallery: [
      {
        src: "/demos/templates/sera-loaves.webp",
        alt: "A counter piled with scored, flour-dusted sourdough loaves",
      },
    ],
    nav: { about: "Our story", pricing: "The menu", contact: "Come by" },
    about: {
      title: "A little flour. A lot of feeling.",
      text: "We start while the neighborhood sleeps. Flour, water, salt, and a very patient starter become the bread you break with your favorite people.",
      principles: [
        [
          "Let it take its time",
          "Long fermentation. Deep flavor. No shortcuts.",
        ],
        [
          "Follow the season",
          "Fruit at its best, folded into something flaky.",
        ],
        [
          "Save you a seat",
          "A neighborhood ritual, one good morning at a time.",
        ],
      ],
    },
    packages: seraPackages,
    faqs: seraFaqs,
    pricingNote:
      "Catering needs 48 hours’ notice. Our kitchen handles wheat, dairy, eggs, sesame, and nuts.",
    contactTitle: "Bring a little Sera to the table.",
    contactNote:
      "Breakfast for eight or a party for twenty-four. Tell us what you have in mind.",
  },
};

export const dailyBake = [
  {
    name: "Country sourdough",
    note: "Our everyday, 36-hour loaf",
    price: "$12",
  },
  {
    name: "Butter croissant",
    note: "A thousand good little layers",
    price: "$5",
  },
  {
    name: "Morning bun",
    note: "Cinnamon, citrus, a little crunch",
    price: "$6",
  },
  {
    name: "Seasonal danish",
    note: "Whatever the market gives us",
    price: "$7",
  },
];

export function demoHref(id: DemoSlug, page: DemoPage = "home") {
  return `/demos/${id}${page === "home" ? "" : `/${page}`}`;
}

/** Use an empty basePath for a standalone client site, or any mounted route. */
export function businessHref(
  business: BusinessTemplate,
  page: DemoPage = "home",
) {
  return `${business.basePath}${page === "home" ? "" : `/${page}`}` || "/";
}
