import type { Metadata } from "next";
import { site } from "@/site";
import { BusinessWebsite } from "@/templates/template-pages";

export const metadata: Metadata = { title: "Request a visit" };

export default function Page() {
  return <BusinessWebsite business={site} page="booking" />;
}
