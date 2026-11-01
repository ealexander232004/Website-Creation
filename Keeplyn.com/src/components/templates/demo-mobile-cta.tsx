"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { useEffect, useState } from "react";

/** Phone-only prompt that slides in once the visitor scrolls past the demo's hero. */
export function DemoMobileCta() {
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const update = () => setShown(window.scrollY > window.innerHeight * 0.6);
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, []);

  return (
    <Link
      href="/start"
      className="template-mobile-cta"
      data-shown={shown}
      aria-hidden={!shown}
      tabIndex={shown ? undefined : -1}
    >
      <span>Want one like this?</span>
      <strong>
        Get a free demo <ArrowUpRight size={15} aria-hidden="true" />
      </strong>
    </Link>
  );
}
