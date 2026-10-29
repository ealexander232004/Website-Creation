import type { Metadata } from "next";
import { Geist } from "next/font/google";
import { site } from "@/site";
import { templateFonts } from "@/templates/typography";
import "./globals.css";
import "@/templates/templates.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: site.name, template: `%s / ${site.name}` },
  description: site.intro,
  openGraph: { title: site.name, description: site.intro, siteName: site.name, type: "website" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${templateFonts}`}>
        <main>{children}</main>
      </body>
    </html>
  );
}
