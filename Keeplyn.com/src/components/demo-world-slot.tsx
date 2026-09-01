"use client";

import dynamic from "next/dynamic";
import type { DemoWorldVariant } from "@/components/demo-three-worlds";

const DemoWorld3D = dynamic(
  () => import("@/components/demo-three-worlds").then((module) => module.DemoWorld3D),
  {
    ssr: false,
    loading: () => <div className="demo-world-loading size-full" aria-hidden="true" />,
  },
);

export function DemoWorld({ variant, className = "" }: { variant: DemoWorldVariant; className?: string }) {
  return <DemoWorld3D variant={variant} className={className} />;
}
