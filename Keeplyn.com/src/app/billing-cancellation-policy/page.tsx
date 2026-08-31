import type { Metadata } from "next";
import { PolicyPage, PolicySection } from "@/components/policy-page";

export const metadata: Metadata = {
  title: "Billing & Cancellation Policy",
  description: "Keeplyn's payment, refund, renewal, and cancellation terms.",
};

export default function BillingCancellationPolicyPage() {
  return (
    <PolicyPage
      currentPath="/billing-cancellation-policy"
      title="Billing & Cancellation"
      summary="What to expect when you purchase, renew, cancel, or request a refund for a Keeplyn service."
    >
      <PolicySection number="01" title="Purchases and authorization">
        <p>
          Prices and billing schedules are shown at checkout, on the pricing page,
          or in an accepted proposal. By purchasing a service, you authorize Keeplyn
          and its payment processor to charge the payment method you provide for the
          listed amount, applicable taxes, and any later charges you approve.
        </p>
      </PolicySection>

      <PolicySection number="02" title="Payment processing">
        <p>
          Payments are processed securely by Stripe. Keeplyn does not store full
          payment card details. Your bank, card issuer, or Stripe may apply separate
          terms, verification steps, currency conversion, or processing times.
        </p>
      </PolicySection>

      <PolicySection number="03" title="Five-business-day full refunds">
        <p>
          <strong>
            Keeplyn offers a full refund when you initiate the request within five
            (5) business days of the original purchase.
          </strong>
        </p>
        <p>
          A request is initiated when you email{" "}
          <a href="mailto:hello@keeplyn.com">hello@keeplyn.com</a> with enough
          information for us to identify the purchase. “Business days” means Monday
          through Friday, excluding U.S. federal holidays. “Original purchase” means
          the initial charge for the applicable service or plan.
        </p>
        <p>
          Approved refunds are returned to the original payment method. We will
          submit the full refund promptly, but Stripe, your bank, or your card issuer
          controls when the credit appears in your account.
        </p>
      </PolicySection>

      <PolicySection number="04" title="Cancellations after the refund window">
        <p>
          You may cancel a one-time project by emailing us. If the five-business-day
          refund window has passed, amounts already paid are non-refundable unless
          your proposal says otherwise or applicable law requires a refund. Any work
          completed, approved expenses, and other amounts due through the cancellation
          date remain payable.
        </p>
      </PolicySection>

      <PolicySection number="05" title="Recurring services and renewals">
        <p>
          Recurring hosting, care, maintenance, or subscription services renew
          automatically at the billing interval disclosed when purchased. You may
          cancel by emailing us before the next renewal date. Cancellation stops
          future renewal charges, and service normally continues through the end of
          the period already paid for.
        </p>
        <p>
          Renewal charges are not part of the original-purchase refund window and are
          non-refundable once processed, except where required by law. Cancel early
          enough for us to process your request before the next billing date.
        </p>
      </PolicySection>

      <PolicySection number="06" title="Failed or overdue payments">
        <p>
          If a payment fails or becomes overdue, we may retry the charge, ask you to
          update your payment method, pause work, or suspend services after reasonable
          notice. You remain responsible for valid outstanding charges and any taxes
          or fees expressly disclosed and permitted by law.
        </p>
      </PolicySection>

      <PolicySection number="07" title="Price changes">
        <p>
          We may change prices for future purchases. For an active recurring service,
          we will provide reasonable advance notice before a new price applies to a
          later billing period, giving you an opportunity to cancel before renewal.
          A signed proposal may contain different price-change terms.
        </p>
      </PolicySection>

      <PolicySection number="08" title="Billing questions and disputes">
        <p>
          Please contact us first if you do not recognize a charge or believe a
          billing error occurred. We will review the account and work to resolve the
          issue. This policy does not limit any non-waivable consumer rights available
          under applicable law.
        </p>
        <p>
          To cancel, request a refund, or ask a billing question, email{" "}
          <a href="mailto:hello@keeplyn.com">hello@keeplyn.com</a>.
        </p>
      </PolicySection>
    </PolicyPage>
  );
}
