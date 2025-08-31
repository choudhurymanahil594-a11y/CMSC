# test_crawler_v2.py
import sys
import os
import asyncio
import json
import random
# import collections # 不再需要 collections 模块
from playwright.async_api import async_playwright

# --- 核心步骤：将 proxy_checker 包添加到 Python 搜索路径 ---
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'proxy_checker'))
if project_path not in sys.path:
    sys.path.append(project_path)
# ---------------------------------------------------------

from proxy_checker.proxy_manager import ProxyManager
from proxy_checker.config import SEMAPHORE_LIMIT

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
    单个爬虫工人，只负责执行一次爬取尝试。
    成功则返回结果，失败则抛出异常。
    """
    browser = None
    try:
        browser = await manager.launch_browser_with_proxy(proxy, headless=True)
        page = await browser.new_page()
        await page.goto(target_url, timeout=30000)
        content = await page.text_content("pre")
        data = json.loads(content)
        return data.get("origin", "IP not found")
    finally:
        if browser:
            await browser.close()

async def task_with_retry(target_url: str, initial_proxy: str, all_proxies: list, manager: ProxyManager, max_retries=3):
    """
    一个带重试逻辑的任务。
    它会尝试最多 max_retries 次，第一次使用 initial_proxy，之后失败则从 all_proxies 中选择。
    """
    # 维护当前任务可用的代理列表，排除已尝试失败的
    current_available_proxies = list(all_proxies) 
    
    # 第一次尝试使用 initial_proxy
    proxy_to_use = initial_proxy
    
    for attempt in range(max_retries):
        if not proxy_to_use: # 如果没有代理可用了（比如 initial_proxy 失败且 all_proxies 也用完了）
            print(f"[TASK FAILED] 任务 {target_url} 失败，已无可用代理进行重试。")
            break # 跳出重试循环

        print(f"[ATTEMPT {attempt + 1}/{max_retries}] 任务 {target_url} -> 使用代理 {proxy_to_use}")
        
        try:
            origin_ip = await crawler_worker(proxy_to_use, manager, target_url)
            print(f"[TASK SUCCESS] 任务 {target_url} 成功 -> 代理 {proxy_to_use} -> 检测到 IP: {origin_ip}")
            return # 任务成功，立即返回
        except Exception as e:
            print(f"[ATTEMPT FAILED] 代理 {proxy_to_use} 失败: {e}")
            
            # 将失败的代理从当前任务的可用代理池中移除，避免再次尝试
            if proxy_to_use in current_available_proxies:
                current_available_proxies.remove(proxy_to_use)
            
            # 如果还有重试次数，选择下一个代理
            if attempt < max_retries - 1 and current_available_proxies:
                proxy_to_use = random.choice(current_available_proxies) # 随机选择下一个代理
            else:
                proxy_to_use = None # 没有更多代理或重试次数用尽
    
    # 如果循环结束仍未成功
    print(f"[TASK FAILED] 任务 {target_url} 在尝试 {max_retries} 次后彻底失败。")
    with open("failed_tasks.txt", "a") as f:
        f.write(target_url + "\n")

async def main():
    """
    主函数，并发调度所有带重试逻辑的任务。
    """
    live_proxies = load_live_proxies()
    if not live_proxies:
        return

    print(f"[CONFIG] 并发任务数限制为: {SEMAPHORE_LIMIT} (在 proxy_checker/config.py 中设置)")

    manager = None
    try:
        async with async_playwright() as p:
            manager = ProxyManager(p)
            
            # 假设我们有多个页面需要爬取
            target_urls = [
                "https://httpbin.org/ip",
                "https://httpbin.org/ip", # 模拟第二个任务
                "https://httpbin.org/ip"  # 模拟第三个任务
            ]
            
            tasks = []
            # 确保代理数量足够，否则循环会提前结束
            num_tasks = min(len(target_urls), len(live_proxies)) 
            
            # 按顺序将 URL 和代理进行绑定
            for i in range(num_tasks):
                url = target_urls[i]
                initial_proxy = live_proxies[i]
                tasks.append(task_with_retry(url, initial_proxy, live_proxies, manager))
            
            # 如果 target_urls 数量多于 live_proxies，剩余的 URL 将不会被处理
            if len(target_urls) > len(live_proxies):
                print(f"[WARNING] 目标 URL 数量 ({len(target_urls)}) 多于可用代理数量 ({len(live_proxies)})。部分 URL 将不会被处理。")

            await asyncio.gather(*tasks)
            
    finally:
        # 所有任务完成后，执行一次清理
        if manager:
            manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
