import { Plus } from "lucide-react";
import { SectionHeading } from "./section-heading";

const faqs = [
  {
    question: "How long does a website take?",
    answer:
      "Most focused small-business websites can be completed in roughly 2–4 weeks once content and feedback are moving. Larger Pro builds may take a little longer. Your specific timeline is agreed before the project starts.",
  },
  {
    question: "What do I need to provide?",
    answer:
      "Your business details, services, preferred contact information, logo if you have one, and any photos you want to use. Keeplyn guides you through the rest with a clear kickoff checklist.",
  },
  {
    question: "Can you help with the words on my website?",
    answer:
      "Yes. Every project includes guidance on structure and key messages. Pro includes deeper messaging and content guidance, while full copywriting can be scoped separately when needed.",
  },
  {
    question: "Do I own my website?",
    answer:
      "Yes. After the project balance is paid, the custom website and approved project assets are yours. Keeplyn can continue hosting and maintaining it through a care plan.",
  },
  {
    question: "What counts as a monthly content update?",
    answer:
      "Common requests include changing text, swapping photos, updating hours, adding a team member, or refreshing an existing service. New pages, features, and redesigns are quoted separately before work begins.",
  },
  {
    question: "Can Keeplyn redesign my current website?",
    answer:
      "Absolutely. The same Starter and Pro paths can be used for a thoughtful redesign. We keep what is working, improve what is not, and plan the transition before launch.",
  },
];

export function FaqSection() {
  return (
    <section id="faq" className="section-space bg-cream">
      <div className="site-container grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
        <div className="lg:sticky lg:top-28 lg:self-start">
          <SectionHeading
            eyebrow="Questions, answered"
            title="The details, without the fine-print fog."
            description="Still deciding what fits? Send a note and get a direct, practical answer."
          />
          <a
            href="mailto:hello@keeplyn.com?subject=Question%20about%20a%20Keeplyn%20website"
            className="mt-7 inline-flex text-sm font-bold text-violet underline decoration-violet/25 underline-offset-4 hover:decoration-violet"
          >
            Ask a different question
          </a>
        </div>

        <div className="divide-y divide-navy/10 border-y border-navy/10">
          {faqs.map((faq, index) => (
            <details key={faq.question} className="faq-item group" open={index === 0}>
              <summary className="flex cursor-pointer list-none items-center justify-between gap-6 py-6 text-left text-base font-bold text-navy sm:text-lg [&::-webkit-details-marker]:hidden">
                {faq.question}
                <span className="grid size-8 shrink-0 place-items-center rounded-full bg-navy/5 text-navy transition-all group-open:rotate-45 group-open:bg-violet group-open:text-white">
                  <Plus className="size-4" aria-hidden="true" />
                </span>
              </summary>
              <p className="max-w-2xl pb-6 pr-10 text-sm leading-7 text-slate sm:text-base">
                {faq.answer}
              </p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
