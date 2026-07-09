import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Live GitHub Pages version
        await page.goto('https://leemind-q.github.io/taewoo-dashboard/')
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.wait_for_timeout(5000)
        await page.screenshot(path='v2_live.png', full_page=True)
        
        await browser.close()
        print('Live v2 screenshot captured')

asyncio.run(main())
