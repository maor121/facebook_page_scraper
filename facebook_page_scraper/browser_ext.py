"""
From: https://github.com/Smartproxy/Selenium-proxy-authentication
"""

import zipfile
from abc import ABC, abstractmethod


class BrowserExtension(ABC):
    @abstractmethod
    def __call__(self):
        pass


class ProxyAuthChromeExtension(BrowserExtension):
    def __init__(self, username, password, endpoint, port):
        self.extension = ProxyAuthChromeExtension.proxies(username, password, endpoint, port)

    def __call__(self):
        return self.extension

    @staticmethod
    def proxies(username, password, endpoint, port):
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxies",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                  },
                  bypassList: ["localhost"]
                }
              };
    
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
    
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }
    
        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (endpoint, port, username, password)

        extension = 'proxies_extension.zip'

        with zipfile.ZipFile(extension, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)

        return extension


class HttpStatusExtention(BrowserExtension):
    def __init__(self):
        self.extention = HttpStatusExtention.http_status_extension()

    def __call__(self):
        return self.extention

    @staticmethod
    def http_status_extension():
        """
        baed on: https://stackoverflow.com/questions/59519156/how-to-get-status-code-in-selenium-chrome-web-driver-in-python
        Save http status in cooky: StatusCodeInCookies, when page is done loading
        """
        manifest_json = """
        {
          "description": "Save http status code in site cookies",
          "manifest_version": 2,
          "name": "StatusCodeInCookies",
          "version": "1.0",
          "permissions": [
            "webRequest", "*://*/*", "cookies"
          ],
          "background": {
            "scripts": [ "background.js" ]
          }
        }
        """

        background_js = """
        //your_js_file_with_extension.js

        var targetPage = "*://*/*";

        function setStatusCodeDiv(e) {
            chrome.cookies.set({
                url: e.url,
                name: 'status-code',
                value: `${e.statusCode}`
            });
        }

        chrome.webRequest.onCompleted.addListener(
          setStatusCodeDiv,
          {urls: [targetPage], types: ["main_frame"]}
        );
        """

        extension = 'http_status_extension.zip'

        with zipfile.ZipFile(extension, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)

        return extension