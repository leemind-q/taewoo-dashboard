import asyncio, os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Local version with full data
        path = os.path.expanduser('~/projects/taewoo-dashboard/index.html')
        await page.goto(f'file://{path}')
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.wait_for_timeout(5000)  # Wait for API calls
        await page.screenshot(path='v2_local.png', full_page=True)
        
        await browser.close()
        print('v2 screenshot captured')

asyncio.run(main())
