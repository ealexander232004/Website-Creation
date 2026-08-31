import Image from "next/image";
import Link from "next/link";

export function BrandLogo() {
  return (
    <Link
      href="/"
      className="group inline-flex size-12 items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mint focus-visible:ring-offset-2 focus-visible:ring-offset-black"
      aria-label="Keeplyn home"
    >
      <Image
        src="/keeplyn-logo-mark.png"
        alt=""
        width={48}
        height={48}
        className="size-12 object-contain transition-transform duration-300 group-hover:-translate-y-0.5"
      />
    </Link>
  );
}
