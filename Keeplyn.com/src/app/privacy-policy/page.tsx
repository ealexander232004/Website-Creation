import type { Metadata } from "next";
import { PolicyPage, PolicySection } from "@/components/policy-page";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "How Keeplyn collects, uses, and protects personal information.",
};

export default function PrivacyPolicyPage() {
  return (
    <PolicyPage
      currentPath="/privacy-policy"
      title="Privacy Policy"
      summary="A straightforward explanation of the information we collect, why we use it, and the choices available to you."
    >
      <PolicySection number="01" title="Scope">
        <p>
          This Privacy Policy explains how Keeplyn collects, uses, discloses, and
          protects personal information when you visit keeplyn.com, contact us,
          request a proposal, purchase services, or otherwise work with us.
        </p>
      </PolicySection>

      <PolicySection number="02" title="Information you provide">
        <p>We may collect information you choose to provide, including:</p>
        <ul>
          <li>Your name, business name, email address, phone number, and contact preferences.</li>
          <li>Project details, messages, files, content, credentials, and feedback.</li>
          <li>Billing contact information and records of purchases and invoices.</li>
          <li>Any other information you include in forms, emails, or meetings.</li>
        </ul>
      </PolicySection>

      <PolicySection number="03" title="Information collected automatically">
        <p>
          When you use our website, we and our service providers may automatically
          receive technical information such as your IP address, browser and device
          type, operating system, referring page, pages viewed, approximate location,
          and dates and times of access. We may use cookies or similar technologies
          to operate the site, remember preferences, understand performance, and
          improve our services.
        </p>
      </PolicySection>

      <PolicySection number="04" title="Payments through Stripe">
        <p>
          Stripe processes payments for Keeplyn. When you pay, your payment details
          are submitted directly to Stripe and are handled under Stripe&apos;s own terms
          and privacy policy. Keeplyn receives transaction details such as payment
          status, amount, date, and limited card information, but does not receive or
          store your full payment card number.
        </p>
      </PolicySection>

      <PolicySection number="05" title="How we use information">
        <p>We may use personal information to:</p>
        <ul>
          <li>Respond to inquiries and provide proposals, projects, support, and website care.</li>
          <li>Process payments, maintain business records, and manage our relationship with you.</li>
          <li>Operate, secure, troubleshoot, analyze, and improve our website and services.</li>
          <li>Send service messages and, where permitted, relevant marketing communications.</li>
          <li>Prevent fraud, enforce agreements, comply with law, and protect rights and safety.</li>
        </ul>
      </PolicySection>

      <PolicySection number="06" title="When we share information">
        <p>
          We do not sell personal information. We may share it with vendors that
          help us operate our business, such as Stripe, hosting providers, email and
          collaboration tools, analytics providers, and professional advisers. We
          may also disclose information when required by law, to protect rights or
          safety, in connection with a business transaction, or with your direction
          or consent.
        </p>
      </PolicySection>

      <PolicySection number="07" title="Retention and security">
        <p>
          We keep personal information only as long as reasonably needed for the
          purposes described here, including providing services, maintaining records,
          resolving disputes, and meeting legal obligations. We use reasonable
          administrative, technical, and organizational safeguards, but no method of
          transmission or storage is completely secure.
        </p>
      </PolicySection>

      <PolicySection number="08" title="Your choices and rights">
        <p>
          You may unsubscribe from marketing emails using the link in the message or
          by contacting us. Your browser can also block or delete cookies, although
          some site features may not work as intended.
        </p>
        <p>
          Depending on where you live, you may have rights to request access,
          correction, deletion, restriction, objection, or portability of personal
          information, or to withdraw consent. We may need to verify your request,
          and legal exceptions may apply.
        </p>
      </PolicySection>

      <PolicySection number="09" title="Children's privacy">
        <p>
          Our services are intended for businesses and are not directed to children
          under 13. We do not knowingly collect personal information from children
          under 13. If you believe a child provided information to us, please contact
          us so we can review and delete it where appropriate.
        </p>
      </PolicySection>

      <PolicySection number="10" title="Updates and contact">
        <p>
          We may update this policy to reflect changes in our practices, technology,
          or legal obligations. The effective date at the top identifies the latest
          revision.
        </p>
        <p>
          To ask a privacy question or submit a request, email{" "}
          <a href="mailto:support@keeplyn.com">support@keeplyn.com</a>.
        </p>
      </PolicySection>
    </PolicyPage>
  );
}
