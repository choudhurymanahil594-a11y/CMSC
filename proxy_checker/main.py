# proxy_checker/main.py
import asyncio
from playwright.async_api import async_playwright

from config import PROXIES
from proxy_manager import ProxyManager

async def main():
    """
    主函数，用于初始化 Playwright 并并发测试所有代理。
    """
    async with async_playwright() as playwright:
        manager = ProxyManager(playwright)
        tasks = [manager.test_single_proxy(proxy) for proxy in PROXIES]
        await asyncio.gather(*tasks)
        if manager: # manager 肯定存在，因为是在 async with 块内创建的
            manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
