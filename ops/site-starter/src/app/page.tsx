import { site } from "@/site";
import { BusinessWebsite } from "@/templates/template-pages";

export default function HomePage() {
  return <BusinessWebsite business={site} page="home" />;
}
