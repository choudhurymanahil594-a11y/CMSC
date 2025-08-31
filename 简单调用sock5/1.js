const puppeteer = require('puppeteer-core');

// 你本地的 Chrome 路径（根据你的系统路径修改）
const chromePath = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

// socks5 代理设置（包含用户名和密码）
const proxy = 'socks5://ivyfyslr:3j05k0cal8uraa@46.202.59.33:5524';

(async () => {
    // 启动浏览器并指定本地 Chrome 路径和代理
    const browser = await puppeteer.launch({
        executablePath: chromePath,  // 指定本地 Chrome 浏览器路径
        headless: false,             // 设置为 false 以便看到浏览器运行
        args: [
            `--proxy-server=${proxy}`,  // 设置 socks5 代理
            '--no-sandbox',              // 防止沙盒问题
            '--disable-setuid-sandbox'   // 另一个防止沙盒问题的参数
        ],
    });

    // 创建一个新的页面
    const page = await browser.newPage();

    // 访问页面
    await page.goto('https://httpbin.org/ip');  // 示例页面，查看返回的 IP 地址

    // 打印页面内容
    const content = await page.content();
    console.log(content);  // 输出页面 HTML

    // 关闭浏览器
    await browser.close();
})();
