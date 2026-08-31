import Link from "next/link";
import { ArrowLeft, ArrowUpRight, LockKeyhole } from "lucide-react";
import { BrandLogo } from "@/components/brand-logo";

export const metadata = {
  title: "Customer Login",
  description: "Access information for the private Keeplyn customer portal.",
};

export default function LoginPage() {
  return (
    <main className="relative grid min-h-screen place-items-center overflow-hidden bg-cream px-4 py-12">
      <div className="hero-grid absolute inset-0 opacity-40 [mask-image:radial-gradient(circle_at_center,black,transparent_75%)]" />
      <div className="absolute left-1/4 top-1/4 size-72 rounded-full bg-mint/30 blur-[90px]" />
      <div className="absolute bottom-1/4 right-1/4 size-72 rounded-full bg-violet/15 blur-[90px]" />

      <section className="relative w-full max-w-md rounded-[2rem] border border-navy/10 bg-white p-7 text-center shadow-[0_32px_80px_-32px_rgba(17,26,46,0.3)] sm:p-10">
        <div className="flex justify-center">
          <BrandLogo />
        </div>
        <div className="mx-auto mt-10 grid size-14 place-items-center rounded-2xl bg-navy text-mint">
          <LockKeyhole className="size-6" aria-hidden="true" />
        </div>
        <p className="mt-6 text-xs font-bold uppercase tracking-[0.16em] text-violet">Customer portal</p>
        <h1 className="mt-3 text-3xl font-bold tracking-[-0.05em] text-navy">Your project, kept close.</h1>
        <p className="mt-4 text-sm leading-6 text-slate">
          The Keeplyn portal is private and invitation-only. Active customers receive a secure access link directly. Need a new invitation or help with access?
        </p>
        <div className="mt-8 grid gap-3">
          <a
            href="mailto:hello@keeplyn.com?subject=Customer%20portal%20access"
            className="button-primary justify-center"
          >
            Get portal help
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </a>
          <Link href="/" className="button-secondary justify-center">
            <ArrowLeft className="size-4" aria-hidden="true" />
            Back to Keeplyn
          </Link>
        </div>
      </section>
    </main>
  );
}
