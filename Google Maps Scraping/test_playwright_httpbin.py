import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from config import PROXIES_DIR
from proxy_manager import ProxyManager

async def main():
    proxies_file = PROXIES_DIR / "proxy-urls.txt"
    manager = ProxyManager(proxy_urls_file=proxies_file)
    proxy = manager.get_next_proxy()
    print("Proxy dict:", proxy.to_playwright_dict() if proxy else None)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            proxy=proxy.to_playwright_dict() if proxy else None,
        )
        page = await context.new_page()
        print("Navigating to httpbin...")
        res = await page.goto("https://httpbin.org/ip", timeout=15000)
        print("Status:", res.status if res else None)
        print("Body:", await page.content())
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
