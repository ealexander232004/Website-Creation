export interface PlanDetailGroup {
  title: string;
  items: string[];
}

export interface WebsitePlan {
  id: "starter" | "pro";
  name: string;
  price: string;
  hosting: string;
  timeline: string;
  summary: string;
  homeFeatures: string[];
  buildDetails: PlanDetailGroup[];
  careDetails: string[];
  featured?: boolean;
}

export const websitePlans: WebsitePlan[] = [
  {
    id: "starter",
    name: "Starter",
    price: "$750",
    hosting: "$49.99/mo",
    timeline: "2–3 weeks",
    summary: "A focused, custom site for one clear service, offer, or local business.",
    homeFeatures: ["Up to 4 pages", "Custom responsive design", "SEO + launch setup"],
    buildDetails: [
      {
        title: "Strategy",
        items: [
          "60-minute kickoff and goal setting",
          "Page plan and conversion path",
          "Light copy editing for supplied content",
        ],
      },
      {
        title: "Design",
        items: [
          "One original visual direction",
          "Up to 4 custom-designed pages",
          "Mobile, tablet, and desktop layouts",
          "Two focused revision rounds",
        ],
      },
      {
        title: "Build & launch",
        items: [
          "Fast, accessible production build",
          "Contact or lead-capture form",
          "Foundational on-page SEO",
          "Analytics and search-console setup",
          "Domain connection and launch support",
        ],
      },
    ],
    careDetails: [
      "Managed hosting and SSL",
      "Daily backups and security updates",
      "Uptime monitoring",
      "30 minutes of content edits each month",
      "Email support within 2 business days",
    ],
  },
  {
    id: "pro",
    name: "Pro",
    price: "$1,500",
    hosting: "$99.99/mo",
    timeline: "4–6 weeks",
    summary: "A deeper website system for a growing business with more to explain, publish, or sell.",
    homeFeatures: ["Up to 8 pages", "CMS + integrations", "Messaging guidance"],
    buildDetails: [
      {
        title: "Strategy",
        items: [
          "90-minute strategy workshop",
          "Full sitemap and conversion planning",
          "Messaging hierarchy and copy guidance",
          "Competitor and positioning review",
        ],
      },
      {
        title: "Design",
        items: [
          "Original visual system and art direction",
          "Up to 8 custom-designed pages",
          "Mobile, tablet, and desktop layouts",
          "Custom motion and interaction design",
          "Three focused revision rounds",
        ],
      },
      {
        title: "Build & launch",
        items: [
          "Everything included in Starter",
          "CMS, blog, or portfolio collection",
          "Scheduling, CRM, or email integrations",
          "Advanced technical SEO and redirects",
          "Performance optimization and launch QA",
          "Recorded handoff and editor training",
        ],
      },
    ],
    careDetails: [
      "Everything in Starter care",
      "90 minutes of content edits each month",
      "Priority support within 1 business day",
      "Monthly performance and SEO check",
      "Quarterly conversion review",
    ],
    featured: true,
  },
];
