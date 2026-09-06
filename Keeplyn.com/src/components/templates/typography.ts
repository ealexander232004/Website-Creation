import { Cormorant_Garamond, Fraunces } from "next/font/google";

const landscape = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["400", "500"],
  style: ["normal", "italic"],
  variable: "--font-landscape",
  display: "swap",
});
const bakery = Fraunces({
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
  style: ["normal", "italic"],
  variable: "--font-bakery",
  display: "swap",
});

export const templateFonts = `${landscape.variable} ${bakery.variable}`;
