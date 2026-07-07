import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        path = os.path.expanduser('~/projects/taewoo-dashboard/index.html')
        await page.goto(f'file://{path}')
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.screenshot(path='dashboard_check.png', full_page=True)
        await browser.close()
        print('Screenshot captured')

asyncio.run(main())
