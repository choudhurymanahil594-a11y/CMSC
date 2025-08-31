# test_crawler.py
import sys
import os
import asyncio
import json
from playwright.async_api import async_playwright

# --- 核心步骤：将 proxy_checker 包添加到 Python 搜索路径 ---
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'proxy_checker'))
if project_path not in sys.path:
    sys.path.append(project_path)
# ---------------------------------------------------------

from proxy_checker.proxy_manager import ProxyManager
from proxy_checker.config import SEMAPHORE_LIMIT # 导入并发限制数量，用于说明

def load_live_proxies(filepath="proxy_checker/proxy-live.txt"):
    """从文件中加载可用的代理列表。"""
    # 确保文件路径是相对于当前脚本的正确路径
    full_filepath = os.path.join(os.path.dirname(__file__), filepath)
    if not os.path.exists(full_filepath):
        print(f"[ERROR] 代理文件未找到: {full_filepath}")
        return []
    with open(full_filepath, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    print(f"[INFO] 从 {full_filepath} 加载了 {len(proxies)} 个可用代理。")
    return proxies

async def crawler_worker(proxy: str, manager: ProxyManager, target_url: str):
    """
    单个爬虫工人，使用指定的代理访问 IP 检测网站。
    """
    browser = None
    try:
        browser = await manager.launch_browser_with_proxy(proxy, headless=True)
        
        page = await browser.new_page()
        await page.goto(target_url, timeout=30000)
        
        content = await page.text_content("pre")
        data = json.loads(content)
        origin_ip = data.get("origin", "IP not found")
        
        print(f"[SUCCESS] 代理 {proxy} -> 检测到 IP: {origin_ip}")
        
    except Exception as e:
        print(f"[FAILED] 代理 {proxy} 访问 {target_url} 失败: {e}")
    finally:
        if browser:
            await browser.close()

async def main():
    """
    主函数，并发调度所有爬虫工人。
    """
    live_proxies = load_live_proxies()
    if not live_proxies:
        return

    print(f"[CONFIG] 并发任务数限制为: {SEMAPHORE_LIMIT} (在 proxy_checker/config.py 中设置)")

    manager = None
    try:
        async with async_playwright() as p:
            manager = ProxyManager(p)
            
            # 为每个可用代理创建一个爬虫任务
            target_url = "https://httpbin.org/ip"
            tasks = [crawler_worker(proxy, manager, target_url) for proxy in live_proxies]
            
            # 并发执行所有任务
            await asyncio.gather(*tasks)
            
    finally:
        # 所有任务完成后，执行一次清理
        if manager:
            manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
