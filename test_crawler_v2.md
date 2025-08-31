# `test_crawler_v2.py` (版本 2) 说明文档

## 概述

`test_crawler_v2.py` 是 `test_crawler.py` 的增强版本，它在外部调用 `proxy_checker` 包的基础上，引入了**代理失败重试机制**。这个脚本模拟了一个更健壮的爬虫任务，它会尝试最多3次来完成对目标 URL 的访问，每次失败时会更换一个不同的代理进行重试。

这个版本旨在演示如何在实际爬虫项目中处理代理的不稳定性，提高任务的成功率。

## 功能

*   从 `proxy_checker/proxy-live.txt` 读取可用代理列表。
*   将 `proxy_checker` 包添加到 Python 搜索路径，以便正确导入 `ProxyManager` 和 `config`。
*   定义 `crawler_worker` 函数，负责使用单个代理执行一次爬取尝试。
*   引入 `task_with_retry` 函数，它是一个包装器，为每个目标 URL 提供重试逻辑：
    *   尝试最多3次。
    *   **初始代理分配**：第一次尝试时，使用 `main` 函数中为该任务按顺序分配的初始代理。
    *   **失败后重试策略**：如果代理失败，将其从当前任务的可用代理池中移除。如果还有重试次数和可用代理，则从剩余的代理中**随机选择**一个进行下一次尝试。
    *   如果所有重试次数都用尽仍未成功，则将失败的 URL 记录到 `failed_tasks.txt` 文件中。
*   `main` 函数并发调度多个 `task_with_retry` 任务（每个任务对应一个目标 URL）。
*   在所有任务完成后，调用 `ProxyManager` 的 `cleanup()` 方法清理临时代理插件文件。

## 如何运行

1.  确保您已安装所有必要的依赖（`playwright`）。
2.  确保 `proxy_checker/proxy-live.txt` 文件存在，并且其中包含可用的代理列表（可以通过运行 `proxy_checker/main.py` 生成）。
3.  在当前目录 (`c:/Users/jy021/Desktop/新建文件夹`) 下打开终端。
4.  运行以下命令：
    ```bash
    python test_crawler_v2.py
    ```

## 预期输出

脚本将打印加载的代理数量、并发任务限制，然后为每个任务（目标 URL）打印其尝试过程。

*   **`[ATTEMPT X/Y] 任务 [target_url] -> 使用代理 [proxy_address]`**: 表示当前任务正在进行第 X 次尝试，并使用了哪个代理。
*   **`[TASK SUCCESS] 任务 [target_url] 成功 -> 代理 [proxy_address] -> 检测到 IP: [detected_ip]`**: 表示任务成功完成。
*   **`[ATTEMPT FAILED] 代理 [proxy_address] 失败: [error_message]`**: 表示当前代理尝试失败。如果还有重试次数和可用代理，将从剩余代理中随机选择一个进行下一次尝试。
*   **`[TASK FAILED] 任务 [target_url] 在尝试 X 次后彻底失败。`**: 表示任务在所有重试次数用尽后仍未成功。
*   **`[WARNING] 目标 URL 数量 (...) 多于可用代理数量 (...)。部分 URL 将不会被处理。`**: 如果 `target_urls` 列表比 `proxy-live.txt` 中的代理数量多，则会显示此警告。
*   最后会显示 `[INFO] 临时代理插件目录已清理。`

如果任务彻底失败，`failed_tasks.txt` 文件将被创建或追加，记录失败的 URL。
