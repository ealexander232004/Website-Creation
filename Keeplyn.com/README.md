# Keeplyn

Keeplyn is an editorial marketing site for a small-business web design and care studio. It includes a responsive homepage, transparent pricing, a dedicated gallery of original concept demos, and a focused contact route with accessible motion throughout.

## Local development

Install dependencies and start the development server:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Quality checks

```bash
npx next typegen
npm run typecheck
npm run lint
npm run build
```

## Stack

- Next.js 16 App Router
- React 19
- Tailwind CSS 4
- TypeScript
- Stripe Checkout, Invoicing, and Tax
- Upstash Redis for durable Stripe webhook idempotency

The repository is connected to Vercel with `Keeplyn.com` configured as the project root.

## Stripe integration

The public pricing page sends approved Starter and Pro website builds to a
Stripe-hosted Checkout Session. The server owns plan IDs and amounts, enables
automatic tax, requires a billing address, and optionally collects a business
tax ID. Optional monthly hosting is intentionally not included in the one-time
website-build payment.

Custom proposals and project balances use Stripe Invoicing in the Dashboard.
The customer pays on Stripe's Hosted Invoice Page; Keeplyn does not collect or
store card data. The webhook endpoint at `/api/stripe/webhook` verifies the raw
request body and processes Checkout, invoice, refund, and credit-note events
idempotently.

### Local test-mode setup

1. Copy `.env.example` to `.env.local`. This file is ignored by Git.
2. In Stripe **test mode** (or a Stripe sandbox), open **Developers → API keys**.
   Rotate the previously shared test secret if it was ever exposed, then put the
   newly rotated `sk_test_...` value in `STRIPE_SECRET_KEY` inside `.env.local`.
   Never put it in a `NEXT_PUBLIC_` variable, commit it, or paste it into chat.
3. Keep `STRIPE_TEST_MODE_ONLY=true` and set
   `KEEPYLN_SITE_URL=http://localhost:3000`.
4. Install the Stripe CLI, sign in, and forward test events:

   ```bash
   stripe listen --forward-to localhost:3000/api/stripe/webhook
   ```

5. Put the CLI-provided test endpoint signing secret in
   `STRIPE_WEBHOOK_SECRET`. Signing secrets are endpoint-specific.
6. Start the app with `npm run dev`, visit `/checkout`, and use Stripe's test
   card `4242 4242 4242 4242` with any future expiry and any CVC. Verify the
   redirect, success page, Stripe payment record, and webhook log.

Local development uses an in-memory webhook event ledger if Upstash is absent.
Production deliberately returns an error until durable Redis is configured.

### Stripe Dashboard configuration

Complete these steps separately in the test environment first:

1. **Business and branding:** Under **Settings**, add Keeplyn's legal/business
   details, support email, statement descriptor, logo, brand colors, privacy
   policy URL, terms URL, and cancellation policy URL. Preview the hosted
   Checkout and invoice pages.
2. **Payments:** Under **Payment methods**, enable only methods Keeplyn intends
   to support. Dynamic Payment Methods can optimize compatible methods; cards
   and Link are the initial recommendation. Leave ACH/bank transfer off until
   Keeplyn has an explicit reconciliation process.
3. **Stripe Tax:** Add the registrations where Keeplyn is legally registered to
   collect tax, set the business origin address, and choose the correct preset
   product tax code and exclusive/inclusive behavior for website-design
   services with a tax professional. Either set that preset in Tax settings or
   put its `txcd_...` value in `STRIPE_WEBSITE_SERVICE_TAX_CODE`. Automatic Tax
   only collects tax where a valid registration exists.
4. **Checkout emails:** Enable successful-payment receipts and review refund and
   dispute notification settings.
5. **Webhook destination:** Under **Developers → Webhooks**, add
   `https://keeplyn.com/api/stripe/webhook` for the deployed environment. Select
   `checkout.session.completed`, `checkout.session.async_payment_succeeded`,
   `checkout.session.async_payment_failed`, `invoice.paid`,
   `invoice.payment_failed`, `invoice.voided`, `charge.refunded`, and
   `credit_note.created`. Copy that destination's signing secret to the matching
   Vercel environment as `STRIPE_WEBHOOK_SECRET`.
6. **Invoicing defaults:** Under **Billing → Invoices**, configure the invoice
   template, memo/footer, payment terms, card/Link payment methods, reminder
   schedule, and Hosted Invoice Page. For each custom project, create or select
   a Customer with email and full billing address, add clear service line items,
   enable automatic tax, and add internal metadata such as `project_id`. Send a
   test invoice and pay it from the Hosted Invoice Page before using live mode.

Stripe setup references: [Checkout](https://docs.stripe.com/payments/checkout),
[automatic tax in Checkout](https://docs.stripe.com/payments/checkout/taxes),
[Hosted Invoice Page](https://docs.stripe.com/invoicing/hosted-invoice-page), and
[webhook signatures](https://docs.stripe.com/webhooks/signature).

### Vercel environment setup

1. Add an Upstash Redis resource from the Vercel Marketplace and connect it to
   this project. Confirm that `UPSTASH_REDIS_REST_URL` and
   `UPSTASH_REDIS_REST_TOKEN` are available in every environment receiving
   Stripe webhooks.
2. Add `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`,
   `STRIPE_TEST_MODE_ONLY=true`, `KEEPYLN_SITE_URL`, and the optional tax code as
   encrypted server environment variables. Use test values for Preview while
   validating the integration.
3. Redeploy after changing environment variables. Send test events from the
   Stripe Dashboard and confirm successful `2xx` deliveries, including a resend
   of the same event to verify deduplication.

For live launch, create new live-mode API and webhook secrets, confirm live Tax
registrations and invoice settings, run an end-to-end low-value payment and
refund, and only then set `STRIPE_TEST_MODE_ONLY=false`. Never reuse a test
webhook signing secret for the live endpoint.
