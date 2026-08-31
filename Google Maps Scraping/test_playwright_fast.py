import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from config import PROXIES_DIR
from proxy_manager import ProxyManager

async def main():
    proxies_file = PROXIES_DIR / "proxy-urls.txt"
    manager = ProxyManager(proxy_urls_file=proxies_file)
    proxy = manager.get_next_proxy()
    print("Using proxy:", proxy.host, proxy.port)

    async with async_playwright() as p:
        print("Launching Chromium...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            proxy=proxy.to_playwright_dict() if proxy else None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-US",
        )
        page = await context.new_page()
        print("Navigating to Google Maps with domcontentloaded...")
        await page.goto("https://www.google.com/maps/search/auto+repair+in+Austin,+TX", wait_until="domcontentloaded", timeout=20000)
        print("Page loaded! Title:", await page.title())
        
        # Check URL
        print("Current URL:", page.url)

        # Wait for feed or article
        try:
            await page.wait_for_selector("div[role='feed'], div[role='article'], a.hfpxzc", timeout=15000)
            cards = await page.locator("div[role='feed'] > div > div[role='article'], div[role='article'], a.hfpxzc").count()
            print(f"Discovered {cards} listing items on page!")
        except Exception as e:
            print("Feed wait timeout:", e)
            print("Page body snippet:", (await page.content())[:500])
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
