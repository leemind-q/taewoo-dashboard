"""Capture premium dashboard references for design comparison"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        refs = [
            ("arc_browser", "https://arc.net"),
            ("linear", "https://linear.app"),
            ("raycast", "https://raycast.com"),
        ]
        
        for name, url in refs:
            try:
                await page.goto(url, timeout=15000)
                await page.wait_for_timeout(3000)
                await page.screenshot(path=f'ref_{name}.png', full_page=False)
                print(f'✅ {name} captured')
            except Exception as e:
                print(f'❌ {name}: {str(e)[:60]}')
        
        await browser.close()

asyncio.run(main())
