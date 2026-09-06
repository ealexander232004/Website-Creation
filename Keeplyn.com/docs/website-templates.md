# Keeplyn website templates

Three complete six-page templates replace the old canvas demos. The live collection lives at `/demos`; each business has a real route under `/demos/moss`, `/demos/northline`, or `/demos/sera`. Existing `?demo=…&page=…` links redirect to the corresponding route.

| Template | Direction | Useful for |
| --- | --- | --- |
| Landscape / Moss & Mortar | Full-screen landscape photography, Cormorant Garamond, staggered portfolio, fine rules, forest ink | Landscapers, architecture, interiors, creative studios |
| Care / Northline | Cobalt identity, natural portraiture, generous white space, graphic service symbols | Dental and wellness practices, professional services |
| Neighborhood / Sera | Cherry red, butter yellow, Fraunces display type, food photography, poster-like menu | Bakeries, cafés, restaurants, independent retail |

## Repository map

`Keeplyn.com` is the Next.js app in a larger repository of lead sourcing and enrichment projects. Its marketing routes, authenticated customer portal, admin screens, Supabase integration, Stripe billing, and Resend lifecycle emails sit outside the demo template system. Vercel builds this app from the repository's `Keeplyn.com` root.

## Adapting a template

- `src/components/templates/catalog.ts` owns typed business records, image references, navigation labels, service packages, FAQs, and common page copy.
- `template-homes.tsx` contains three independent homepage compositions. Sector-specific section headings and arrangements live here.
- `template-pages.tsx` renders the home, about, FAQ, pricing/menu, contact, and booking pages through `BusinessWebsite`.
- `template-chrome.tsx` supplies the business header, wordmark, footer, image component, and navigation. The Keeplyn demo switcher is a separate component in the route layout.
- `templates.css` scopes the three design systems under `.template-moss`, `.template-northline`, and `.template-sera`. The `id` selects the visual family, while `basePath` controls business navigation.
- `typography.ts` loads the display fonts only on demo routes and the collection.

Copy a business record, keeping its `id` to choose a visual family. Set `basePath` to the new website's route root (`""` for a standalone site), update its name, optional two-line wordmark, location, images, copy, services, and FAQs, then pass it to `BusinessWebsite`. Mount the six routes with the matching `page` property. Include `templateFonts` on the parent and import `templates.css` once. Review the sector-specific homepage copy and brand sublabel for the new business. Use the existing demo routes as the route and metadata pattern.

For example:

```tsx
const business: BusinessTemplate = {
  ...templates.moss,
  name: "Field Landscape Studio",
  wordmark: ["Field", "Landscape Studio"],
  basePath: "",
  location: "Portland, Oregon",
  // Replace the remaining demo contact details, photographs and content.
};

<BusinessWebsite business={business} page="home" />
```

The component keeps form values in memory and validates required fields, email, dates, and preferred time before showing a preview receipt. Demo submissions never send email, save personal information, make an appointment, or place an order. For a real business, replace `TemplateForm` with its approved booking/contact integration, update availability and submission messages, and remove the concept-business notice. No production backend is implied by these templates.

## Images

Six original GPT Image 2 photographs were created through the built-in image tool. Optimized WebP assets live in `public/demos/templates/`, total approximately 1.8 MB before responsive Next.js image delivery. Hero images load eagerly; supporting images load lazily. The exact generation prompts and asset mapping are in `template-image-prompts.json`. These portray concept businesses, not real clients or patients.

## Design research

Original implementations; no purchased template code or third-party template assets were copied. Reference browsing included [Webflow's bakery collection](https://webflow.com/templates/search/bakery), [Bakers by TNCFlow](https://tncflow.com/template/bakers/), and [Verdant landscape studio](https://www.behance.net/gallery/248170091/Verdant-Landscape-Studio-Design-Website). The common visual principle was to give the business photography and identity priority over generic interface panels.

## Verification

Run the app's `typecheck`, `lint`, and production `build`. Browser checks cover the three homepages at desktop and mobile widths, all eighteen page routes, real navigation and browser back, FAQ disclosure, mobile menus, form validation and preview receipts, old query redirects, image loading, and reduced motion. The release follows `AGENTS.md`: scoped feature-branch commit, GitHub PR and merge, then confirmation of the merged commit's production deployment.
