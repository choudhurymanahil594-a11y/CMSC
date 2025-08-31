# `test_crawler.py` (版本 1) 说明文档

## 概述

`test_crawler.py` 是一个外部测试脚本，用于演示如何从 `proxy_checker` 包中调用 `ProxyManager` 类来执行基本的代理测试。它从 `proxy_checker/proxy-live.txt` 文件中加载可用代理，并使用这些代理并发访问 IP 检测网站 (`https://httpbin.org/ip`)。

这个版本主要关注于验证 `ProxyManager` 的基本集成和并发执行能力，不包含代理失败重试逻辑。

## 功能

*   从 `proxy_checker/proxy-live.txt` 读取可用代理列表。
*   将 `proxy_checker` 包添加到 Python 搜索路径，以便正确导入 `ProxyManager` 和 `config`。
*   使用 `ProxyManager` 并发启动多个带代理的浏览器实例。
*   每个浏览器实例访问 `https://httpbin.org/ip`，并打印检测到的 IP 地址。
*   在所有任务完成后，调用 `ProxyManager` 的 `cleanup()` 方法清理临时代理插件文件。

## 如何运行

1.  确保您已安装所有必要的依赖（`playwright`）。
2.  确保 `proxy_checker/proxy-live.txt` 文件存在，并且其中包含可用的代理列表（可以通过运行 `proxy_checker/main.py` 生成）。
3.  在当前目录 (`c:/Users/jy021/Desktop/新建文件夹`) 下打开终端。
4.  运行以下命令：
    ```bash
    python test_crawler.py
    ```

## 预期输出

脚本将打印加载的代理数量、并发任务限制，然后为每个代理打印其访问 `https://httpbin.org/ip` 的结果。成功的访问会显示 `[SUCCESS] 代理 [proxy_address] -> 检测到 IP: [detected_ip]`，失败的访问会显示 `[FAILED] 代理 [proxy_address] 访问 [target_url] 失败: [error_message]`。最后会显示 `[INFO] 临时代理插件目录已清理。`
