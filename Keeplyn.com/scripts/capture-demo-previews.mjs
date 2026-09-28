// Captures the homepage of each demo template for the Keeplyn marketing pages.
//
// Usage (with `npm run dev` running):
//   npm i --no-save playwright-core
//   CHROME_PATH=/path/to/chrome node scripts/capture-demo-previews.mjs
//
// Writes public/demos/previews/<slug>-fold.webp (first screen) and
// <slug>-full.webp (whole homepage). Recapture whenever a template changes.
import { chromium } from "playwright-core";
import sharp from "sharp";

const base = process.env.BASE_URL ?? "http://localhost:3000";
const slugs = ["moss", "northline", "sera"];
const out = new URL("../public/demos/previews/", import.meta.url);

const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || undefined,
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  reducedMotion: "reduce",
});
for (const slug of slugs) {
  const page = await context.newPage();
  await page.goto(`${base}/demos/${slug}`, { waitUntil: "networkidle" });
  // Show the business website only: no Keeplyn demo bar or dev overlay.
  await page.addStyleTag({
    content: ".template-toolbar, nextjs-portal { display: none !important; }",
  });
  const height = await page.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < height; y += 600) {
    await page.evaluate((top) => window.scrollTo(0, top), y);
    await page.waitForTimeout(80);
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.evaluate(() => document.fonts.ready);
  const full = await page.screenshot({ fullPage: true });
  await sharp(full)
    .extract({ left: 0, top: 0, width: 1440, height: 900 })
    .webp({ quality: 80 })
    .toFile(new URL(`${slug}-fold.webp`, out).pathname);
  const info = await sharp(full)
    .resize({ width: 900 })
    .webp({ quality: 74 })
    .toFile(new URL(`${slug}-full.webp`, out).pathname);
  console.log(`${slug}: 1440x900 fold, 900x${info.height} full`);
  await page.close();
}
await browser.close();
