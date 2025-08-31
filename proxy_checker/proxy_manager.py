# proxy_checker/proxy_manager.py
import os
import tempfile
import asyncio
import json
import shutil # 新增导入
from playwright.async_api import async_playwright

from config import CHROME_PATH, SEMAPHORE_LIMIT

class ProxyManager:
    def __init__(self, playwright_instance, chrome_path=CHROME_PATH):
        """
        初始化 ProxyManager。

        Args:
            playwright_instance: Playwright 实例。
            chrome_path (str): Chrome 浏览器可执行文件路径。
        """
        self.playwright = playwright_instance
        self.chrome_path = chrome_path
        self.semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)

    async def launch_browser_with_proxy(self, proxy: str, headless=False, window_size="1200,800"):
        """
        使用指定的代理启动一个新的浏览器实例。

        Args:
            proxy (str): 代理字符串，格式为 "ip:port:username:password"。
            headless (bool): 是否以无头模式运行浏览器。
            window_size (str): 浏览器窗口大小，例如 "1200,800"。

        Returns:
            playwright.async_api.Browser: 配置好代理的浏览器实例。
        """
        async with self.semaphore:
            try:
                plugin_dir = self._create_proxy_plugin(proxy)

                browser = await self.playwright.chromium.launch(
                    headless=headless,
                    executable_path=self.chrome_path,
                    args=[
                        f"--disable-extensions-except={plugin_dir}",
                        f"--load-extension={plugin_dir}",
                        f"--window-size={window_size}"
                    ]
                )
                print(f"[INFO] 成功使用代理 {proxy} 启动浏览器。")
                return browser
            except Exception as e:
                print(f"[ERROR] 启动浏览器失败，代理 {proxy} -> {e}")
                raise # 重新抛出异常，让调用者知道启动失败

    async def test_single_proxy(self, proxy: str, timeout=15000):
        """
        测试单个代理是否可用，并返回其状态。

        Args:
            proxy (str): 代理字符串，格式为 "ip:port:username:password"。
            timeout (int): 页面加载超时时间（毫秒）。

        Returns:
            bool: 如果代理可用则返回 True，否则返回 False。
        """
        try:
            browser = await self.launch_browser_with_proxy(proxy, headless=True) # 测试时使用无头模式
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://httpbin.org/ip", timeout=timeout)

            text = await page.text_content("pre")
            data = json.loads(text)
            if "origin" in data:
                print(f"[LIVE] {proxy}")
                with open("proxy-live.txt", "a") as f:
                    f.write(proxy + "\n")
                return True
            else:
                print(f"[DEAD] {proxy} -> IP 地址未在响应中找到。")
                return False
        except Exception as e:
            print(f"[DEAD] {proxy} -> {e}")
            return False
        finally:
            if 'browser' in locals() and browser:
                await browser.close()

    def _create_proxy_plugin(self, proxy: str) -> str:
        """
        私有方法：创建 Chrome 代理扩展插件。
        """
        ip, port, username, password = proxy.split(":")
        port = int(port)
        
        # 使用一个更稳定的临时目录，或者让用户配置
        # 这里我们直接在当前工作目录创建一个临时目录，方便管理和清理
        plugin_base_dir = os.path.join(os.getcwd(), "tmp_proxy_plugins")
        os.makedirs(plugin_base_dir, exist_ok=True)
        
        # 为每个代理创建一个唯一的插件目录
        plugin_dir = os.path.join(plugin_base_dir, f"proxy_ext_{ip}_{port}")
        os.makedirs(plugin_dir, exist_ok=True)

        manifest_json = f"""
        {{
            "version":"1.0.0",
            "manifest_version": 2,
            "name":"Chrome Proxy",
            "permissions": ["proxy","tabs","unlimitedStorage","storage","<all_urls>","webRequest","webRequestBlocking"],
            "background": {{"scripts": ["background.js"]}}
        }}
        """
        background_js = f"""
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "socks5",
                    host: "{ip}",
                    port: {port}
                }}
            }}
        }};
        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{username}",
                    password: "{password}"
                }}
            }};
        }}

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
        """
        with open(os.path.join(plugin_dir, "manifest.json"), "w") as f:
            f.write(manifest_json)
        with open(os.path.join(plugin_dir, "background.js"), "w") as f:
            f.write(background_js)
        
        return plugin_dir

    def cleanup(self):
        """
        清理所有生成的临时代理插件目录。
        """
        plugin_base_dir = os.path.join(os.getcwd(), "tmp_proxy_plugins")
        if os.path.exists(plugin_base_dir):
            shutil.rmtree(plugin_base_dir)
            print("[INFO] 临时代理插件目录已清理。")
