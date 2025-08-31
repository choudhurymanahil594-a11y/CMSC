from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import zipfile
import tempfile
import os

# 代理信息
ip = '46.202.59.33'
port = 5524
username = 'ivyfyslr'
password = '3j05k0cal8uraa'

# 生成临时插件文件夹
with tempfile.TemporaryDirectory() as tmpdirname:
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

    plugin_file = os.path.join(tmpdirname, 'proxy_auth_plugin.zip')
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    # Chrome 配置
    options = Options()
    options.add_argument("--start-maximized")  # 最大化窗口
    options.add_argument("--window-size=1200,800")  # 也可以自定义大小
    options.add_extension(plugin_file)
    options.add_argument("--disable-extensions-except=" + plugin_file)  # 仅加载代理插件，加快启动
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")  # 0=INFO, 1=WARNING, 2=ERROR, 3=FATAL

    # 启动浏览器
    browser = webdriver.Chrome(options=options)
    browser.get('https://httpbin.org/ip')
    print(browser.page_source)
    browser.quit()  # 浏览器关闭后临时文件会自动删除
