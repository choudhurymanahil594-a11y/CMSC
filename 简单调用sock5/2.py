import os
import tempfile
import asyncio
import json
from playwright.async_api import async_playwright

proxies = [
    '46.202.59.143:5634:ivyfyslr:3j05k0cal8uraa',
    '23.229.126.88:7617:ivyfyslr:3j05k0cal8uraa',
    '46.202.59.33:5524:ivyfyslr:3j05k0cal8uraa',
    '64.64.110.122:6645:ivyfyslr:3j05k0cal8uraa',
    '50.114.98.58:5542:ivyfyslr:3j05k0cal8uraa',
    '23.26.71.17:5500:ivyfyslr:3j05k0cal8uraa',
    '161.123.154.140:6670:ivyfyslr:3j05k0cal8uraa',
    '50.114.15.232:6217:ivyfyslr:3j05k0cal8uraa',
    '161.123.154.180:6710:ivyfyslr:3j05k0cal8uraa',
    '198.23.239.178:6584:ivyfyslr:3j05k0cal8uraa',
    '198.144.190.240:6087:ivyfyslr:3j05k0cal8uraa',
    '198.144.190.67:5914:ivyfyslr:3j05k0cal8uraa',
    '192.186.172.149:9149:ivyfyslr:3j05k0cal8uraa',
    '192.186.151.100:8601:ivyfyslr:3j05k0cal8uraa',
    '192.186.172.221:9221:ivyfyslr:3j05k0cal8uraa',
    '31.58.30.109:6691:ivyfyslr:3j05k0cal8uraa',
    '31.58.10.162:6130:ivyfyslr:3j05k0cal8uraa',
    '31.58.10.242:6210:ivyfyslr:3j05k0cal8uraa',
    '31.59.13.40:6310:ivyfyslr:3j05k0cal8uraa',
    '145.223.58.13:6282:ivyfyslr:3j05k0cal8uraa',
    '198.20.191.101:5171:ivyfyslr:3j05k0cal8uraa',
    '23.236.222.207:7238:ivyfyslr:3j05k0cal8uraa',
    '23.236.216.186:6216:ivyfyslr:3j05k0cal8uraa',
    '146.103.44.105:6657:ivyfyslr:3j05k0cal8uraa',
    '145.223.56.176:7228:ivyfyslr:3j05k0cal8uraa',
    '145.223.56.143:7195:ivyfyslr:3j05k0cal8uraa',
    '161.123.93.183:5913:ivyfyslr:3j05k0cal8uraa',
    '136.0.194.80:6817:ivyfyslr:3j05k0cal8uraa',
    '173.211.68.54:6336:ivyfyslr:3j05k0cal8uraa',
    '208.70.11.217:6298:ivyfyslr:3j05k0cal8uraa',
    '45.61.100.165:6433:ivyfyslr:3j05k0cal8uraa',
    '136.0.126.109:5870:ivyfyslr:3j05k0cal8uraa',
    '23.27.196.186:6555:ivyfyslr:3j05k0cal8uraa',
    '142.111.44.2:5714:ivyfyslr:3j05k0cal8uraa',
    # ... 继续添加剩下的
]

chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
semaphore = asyncio.Semaphore(5)  # 同时最多5个任务

def create_proxy_plugin(proxy, plugin_path):
    ip, port, username, password = proxy.split(":")
    port = int(port)
    os.makedirs(plugin_path, exist_ok=True)

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
    with open(os.path.join(plugin_path, "manifest.json"), "w") as f:
        f.write(manifest_json)
    with open(os.path.join(plugin_path, "background.js"), "w") as f:
        f.write(background_js)

async def test_proxy(proxy, playwright):
    async with semaphore:
        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                plugin_dir = os.path.join(tmpdirname, "proxy_extension")
                create_proxy_plugin(proxy, plugin_dir)

                browser = await playwright.chromium.launch(
                    headless=False,
                    executable_path=chrome_path,
                    args=[
                        f"--disable-extensions-except={plugin_dir}",
                        f"--load-extension={plugin_dir}",
                        "--window-size=1200,800"
                    ]
                )

                context = await browser.new_context()
                page = await context.new_page()
                await page.goto("https://httpbin.org/ip", timeout=15000)
                print(f"测试代理 {proxy} 的网页内容: {await page.html()}")
                # 解析返回 JSON
                text = await page.text_content("pre")
                data = json.loads(text)
                if "origin" in data:
                    with open("proxy-live.txt", "a") as f:
                        f.write(proxy + "\n")
                    print(f"[LIVE] {proxy}")

                await browser.close()
        except Exception as e:
            print(f"[DEAD] {proxy} -> {e}")

async def main():
    async with async_playwright() as playwright:
        tasks = [test_proxy(proxy, playwright) for proxy in proxies]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
