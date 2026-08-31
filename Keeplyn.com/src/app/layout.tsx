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
    default: "Keeplyn / The Springboard for Your Small Business",
    template: "%s / Keeplyn",
  },
  description:
    "Strategy, design, development, and ongoing website care for small businesses that have outgrown the starter site.",
  keywords: [
    "small business websites",
    "web design",
    "website development",
    "Keeplyn",
  ],
  openGraph: {
    title: "Keeplyn / The Springboard for Your Small Business",
    description:
      "Original, hard-working websites for small businesses ready to look unmistakably themselves.",
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
      <body className="flex min-h-full flex-col overflow-x-hidden">
        {children}
      </body>
    </html>
  );
}
