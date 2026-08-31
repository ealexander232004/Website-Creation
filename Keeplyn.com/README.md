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
