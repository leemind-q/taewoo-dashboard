import asyncio, os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Current live version for comparison
        await page.goto('https://leemind-q.github.io/taewoo-dashboard/')
        await page.wait_for_timeout(4000)
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.screenshot(path='before_redesign.png', full_page=True)
        
        await browser.close()
        print('Reference captured')

asyncio.run(main())
