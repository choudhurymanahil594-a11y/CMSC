
        var config = {
            mode: "fixed_servers",
            rules: {
                singleProxy: {
                    scheme: "socks5",
                    host: "145.223.58.13",
                    port: 6282
                }
            }
        };
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "ivyfyslr",
                    password: "3j05k0cal8uraa"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
        );
        