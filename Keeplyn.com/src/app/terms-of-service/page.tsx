import type { Metadata } from "next";
import { PolicyPage, PolicySection } from "@/components/policy-page";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "The terms that govern use of Keeplyn's website and services.",
};

export default function TermsOfServicePage() {
  return (
    <PolicyPage
      currentPath="/terms-of-service"
      title="Terms of Service"
      summary="The working agreement for using our website and engaging Keeplyn for design, development, hosting, and website care."
    >
      <PolicySection number="01" title="Acceptance of these terms">
        <p>
          These Terms of Service govern your access to keeplyn.com and any
          services provided by Keeplyn. By using the website, requesting a
          proposal, or purchasing a service, you agree to these terms and to any
          proposal or statement of work you accept.
        </p>
        <p>
          If a signed proposal or other written agreement conflicts with these
          terms, that agreement controls for the services it covers.
        </p>
      </PolicySection>

      <PolicySection number="02" title="Services and project scope">
        <p>
          Keeplyn provides website strategy, design, development, hosting,
          maintenance, content updates, and related services. The specific
          deliverables, schedule, revision limits, and fees for a project are
          described in the applicable proposal, order, or plan description.
        </p>
        <p>
          Requests outside an agreed scope may require a revised timeline and
          additional fees, which we will communicate before beginning that work.
        </p>
      </PolicySection>

      <PolicySection number="03" title="Your responsibilities">
        <p>You agree to:</p>
        <ul>
          <li>Provide accurate information, feedback, approvals, and materials on time.</li>
          <li>Make sure you have the right to use all content and assets you provide.</li>
          <li>Review deliverables and promptly identify requested corrections.</li>
          <li>Use the website and services only for lawful purposes.</li>
        </ul>
        <p>
          Delays in receiving required materials, access, or approvals may move
          the project schedule.
        </p>
      </PolicySection>

      <PolicySection number="04" title="Fees and payment">
        <p>
          You agree to pay the fees, taxes, and approved expenses shown at
          checkout or in your proposal. Payments are processed by Stripe or
          another disclosed payment provider. Keeplyn does not store full card
          details.
        </p>
        <p>
          Recurring services renew at the interval shown when purchased until
          canceled. Refunds and cancellations are governed by our{" "}
          <a href="/billing-cancellation-policy">Billing &amp; Cancellation Policy</a>.
        </p>
      </PolicySection>

      <PolicySection number="05" title="Ownership and licenses">
        <p>
          You retain ownership of materials you provide. Keeplyn retains its
          pre-existing tools, methods, templates, know-how, and reusable code.
          Ownership or license rights in final project deliverables are defined
          in the applicable proposal and generally take effect after full payment.
        </p>
        <p>
          Unless we agree to confidentiality in writing, you allow Keeplyn to
          identify you as a client and display completed work in our portfolio
          and marketing materials.
        </p>
      </PolicySection>

      <PolicySection number="06" title="Acceptable use">
        <p>
          You may not use our website, deliverables, or services to violate law,
          infringe another person&apos;s rights, distribute malicious code, gain
          unauthorized access, interfere with service operation, or send abusive,
          deceptive, or unlawful content.
        </p>
      </PolicySection>

      <PolicySection number="07" title="Third-party services">
        <p>
          Projects may rely on third-party products such as domain registrars,
          hosting platforms, analytics tools, plugins, fonts, or Stripe. Those
          services have their own terms, privacy practices, availability, and
          fees. Keeplyn is not responsible for a third party&apos;s acts, outages,
          policy changes, or discontinuation.
        </p>
      </PolicySection>

      <PolicySection number="08" title="Availability and warranties">
        <p>
          We aim to provide reliable, professional services, but the website and
          services are provided on an “as available” basis. To the fullest extent
          allowed by law, we disclaim implied warranties, including merchantability,
          fitness for a particular purpose, and non-infringement. We do not promise
          uninterrupted operation, specific search rankings, traffic, sales, or
          other business outcomes.
        </p>
      </PolicySection>

      <PolicySection number="09" title="Limitation of liability">
        <p>
          To the fullest extent allowed by law, Keeplyn will not be liable for
          indirect, incidental, special, consequential, exemplary, or punitive
          damages, or for lost profits, data, revenue, goodwill, or business
          opportunities. Keeplyn&apos;s total liability relating to a claim will not
          exceed the amount you paid Keeplyn for the service giving rise to the
          claim during the six months before the event occurred.
        </p>
        <p>
          Some jurisdictions do not allow certain exclusions or limits, so these
          limits apply only to the extent permitted by applicable law.
        </p>
      </PolicySection>

      <PolicySection number="10" title="Suspension and termination">
        <p>
          Either party may end services as allowed by the applicable proposal or
          our Billing &amp; Cancellation Policy. We may suspend access or services
          for nonpayment, unlawful use, security risk, or a material breach of
          these terms. Provisions that by their nature should survive termination
          will remain in effect.
        </p>
      </PolicySection>

      <PolicySection number="11" title="Changes, law, and contact">
        <p>
          We may update these terms as our services change. The effective date at
          the top shows the latest revision. Continued use after an update means
          you accept the revised terms. Applicable law determines governing law
          and venue unless a written agreement states otherwise.
        </p>
        <p>
          Questions about these terms can be sent to{" "}
          <a href="mailto:support@keeplyn.com">support@keeplyn.com</a>.
        </p>
      </PolicySection>
    </PolicyPage>
  );
}
