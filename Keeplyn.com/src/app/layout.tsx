import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://keeplyn.com"),
  title: {
    default: "Keeplyn | Modern Websites for Small Businesses",
    template: "%s | Keeplyn",
  },
  description:
    "Keeplyn builds premium, conversion-focused websites for small businesses with straightforward pricing and ongoing support.",
  keywords: [
    "small business websites",
    "web design",
    "website development",
    "Keeplyn",
  ],
  openGraph: {
    title: "Keeplyn | Better Websites for Growing Businesses",
    description:
      "Modern, trustworthy websites built to help small businesses earn attention and turn visits into inquiries.",
    url: "https://keeplyn.com",
    siteName: "Keeplyn",
    type: "website",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col overflow-x-hidden">{children}</body>
    </html>
  );
}
