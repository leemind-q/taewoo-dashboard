import asyncio, os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        path = os.path.expanduser('~/projects/taewoo-dashboard/index.html')
        await page.goto(f'file://{path}')
        await page.set_viewport_size({"width": 1920, "height": 1080})
        # Wait for data to load
        await page.wait_for_timeout(3000)
        # Full page
        await page.screenshot(path='dashboard_full.png', full_page=True)
        # Also capture the live GitHub Pages version
        await page.goto('https://leemind-q.github.io/taewoo-dashboard/')
        await page.wait_for_timeout(3000)
        await page.screenshot(path='dashboard_live.png', full_page=True)
        await browser.close()
        print('Both screenshots captured')

asyncio.run(main())
