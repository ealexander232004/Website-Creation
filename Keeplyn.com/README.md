# Keeplyn

Keeplyn is an editorial marketing site for a small-business web design and care studio. It includes a responsive homepage, transparent pricing, a dedicated gallery of original concept demos, and a focused contact route with accessible motion throughout.

## Local development

Install dependencies and start the development server:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Copy `.env.example` to `.env.local` and add the public Supabase project URL and
publishable key. The customer request flow uses cookie-based Supabase Auth,
private Storage uploads, and the schema in `supabase/migrations`.

The production customer lifecycle also expects these server-side variables,
which are provisioned for Keeplyn through Vercel Marketplace integrations:

- `STRIPE_SECRET_KEY` and `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- `STRIPE_STARTER_BUILD_PRICE_ID` and `STRIPE_PRO_BUILD_PRICE_ID`
- `STRIPE_STARTER_HOSTING_PRICE_ID` and `STRIPE_PRO_HOSTING_PRICE_ID`
- `STRIPE_WEBHOOK_SECRET` and `DATABASE_WEBHOOK_SECRET`
- `RESEND_API_KEY` and `RESEND_EMAIL_DOMAIN`

Stripe Checkout is only available after a customer approves a demo and enters
a domain. Resend sends request, demo, revision, payment, and launch updates from
`updates@keeplyn.com`. Keep `STRIPE_TAX_ENABLED` disabled until the connected
Stripe account has active tax registrations.

Email confirmation redirects must allow both `http://localhost:3000/**` and the
deployed Keeplyn domain in Supabase Auth URL Configuration.

## Quality checks

```bash
npm run typecheck
npm run lint
npm run build
```

## Stack

- Next.js 16 App Router
- React 19
- Tailwind CSS 4
- TypeScript

The repository is connected to Vercel with `Keeplyn.com` configured as the project root.
