import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from config import PROXIES_DIR
from proxy_manager import ProxyManager

async def main():
    proxies_file = PROXIES_DIR / "proxy-urls.txt"
    manager = ProxyManager(proxy_urls_file=proxies_file)
    proxy = manager.get_next_proxy()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            proxy=proxy.to_playwright_dict() if proxy else None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-US",
        )
        page = await context.new_page()
        print("Navigating to google.com/maps with commit...")
        await page.goto("https://www.google.com/maps?hl=en", wait_until="commit", timeout=15000)
        print("Committed! Waiting 5s...")
        await page.wait_for_timeout(5000)
        print("Title:", await page.title())
        print("URL:", page.url)
        content = await page.content()
        print("Content length:", len(content))
        print("Snippet:", content[:400])
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
