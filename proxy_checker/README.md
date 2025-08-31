# Proxy Checker

这是一个用于并发测试 SOCKS5 代理可用性的 Python 项目。它使用 Playwright 启动 Chrome 浏览器，并通过代理扩展来验证代理是否正常工作。

## 项目结构

```
proxy_checker/
├── __init__.py         # 声明这是一个 Python 包
├── main.py             # 主程序入口，用于独立测试所有代理
├── config.py           # 配置文件，包含代理列表、Chrome 路径和并发限制
└── proxy_manager.py    # 核心文件，包含 ProxyManager 类，提供代理管理和浏览器启动功能
```

## 安装

1.  **克隆仓库** (如果这是一个 Git 仓库) 或将文件下载到本地。
2.  **安装 Playwright**:
    ```bash
    pip install playwright
    playwright install chromium
    ```
3.  **安装其他依赖**:
    ```bash
    pip install asyncio
    ```
    (asyncio 和 json 通常是 Python 内置的，但为了完整性列出)

## 配置

编辑 `proxy_checker/config.py` 文件：

*   `PROXIES`: 您的代理服务器列表。每个代理字符串的格式应为 `"ip:port:username:password"`。
*   `CHROME_PATH`: 您的 Chrome 浏览器可执行文件的完整路径。例如：`"C:/Program Files/Google/Chrome/Application/chrome.exe"`。
*   `SEMAPHORE_LIMIT`: 并发任务的数量限制。

## 使用

### 独立运行代理测试

在项目根目录 (`proxy_checker/`) 下运行 `main.py` 文件：

```bash
python main.py
```

程序将并发测试 `config.py` 中定义的代理。可用的代理将被写入 `proxy-live.txt` 文件，不可用的代理将在控制台输出错误信息。

### 在您的爬虫项目中调用 `ProxyManager`

您可以将 `proxy_checker` 作为一个 Python 包导入到您的爬虫项目中。

**方法一：将项目路径添加到 `sys.path` (推荐)**

在您的爬虫项目的代码开头添加以下内容：

```python
import sys
import os

# 假设您的爬虫项目和 proxy_checker 在同一个父目录下
# 如果不在，请调整 project_path 以指向 proxy_checker 目录的绝对路径
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'proxy_checker'))
sys.path.append(project_path)

# 现在您可以像调用普通库一样调用它了
from playwright.async_api import async_playwright
from proxy_checker.proxy_manager import ProxyManager

async def my_crawler():
    async with async_playwright() as p:
        manager = ProxyManager(p)
        
        # 从您的代理池或 API 获取代理字符串
        my_proxy = "ip:port:user:pass" 
        
        # 启动一个带代理的浏览器实例
        browser = await manager.launch_browser_with_proxy(my_proxy, headless=False)
        
        # 您现在可以像往常一样使用这个 browser 实例进行爬取
        page = await browser.new_page()
        await page.goto("https://example.com")
        print(f"Page title: {await page.title()}")
        # ... 您的爬虫逻辑 ...
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(my_crawler())
```

**方法二：将 `proxy_checker` 安装为可编辑模式**

在您的虚拟环境中，进入 `proxy_checker` 目录，然后运行：

```bash
pip install -e .
```

安装后，您就可以在任何项目中直接 `from proxy_checker.proxy_manager import ProxyManager`。

## 输出

*   **[LIVE]**: 表示代理可用，并已写入 `proxy-live.txt`。
*   **[DEAD]**: 表示代理不可用，并显示错误信息。
*   **[INFO]**: 浏览器启动信息。
*   **[ERROR]**: 浏览器启动失败信息。

## 注意事项

*   请确保 `CHROME_PATH` 指向正确的 Chrome 浏览器可执行文件。
*   `proxy-live.txt` 文件将在当前工作目录（即运行 `main.py` 或调用 `ProxyManager` 的目录）中创建或追加。
*   `_create_proxy_plugin` 方法会在当前工作目录创建一个 `tmp_proxy_plugins` 目录来存放临时代理扩展文件。`ProxyManager` 提供了 `cleanup()` 方法来自动清理这些临时文件。
