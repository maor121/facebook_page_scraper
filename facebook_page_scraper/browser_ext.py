"""
From: https://github.com/Smartproxy/Selenium-proxy-authentication
"""
import random
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
        manifest_v2 = random.randint(2,10)
        manifest_v = [random.randint(0,2), random.randint(0,4), random.randint(0,3)]
        random_fruit = random.choice(['apple', 'banana', 'cherry', 'date', 'elderberry', 'fig', 'grape', 'honeydew',
                                      'kiwi', 'lemon', 'mango', 'nectarine', 'orange', 'papaya', 'quince',
                                      'raspberry', 'strawberry', 'tangerine', 'watermelon'])
        backgroun_js_name: str = random.choice(['baground.js',
                                           'bacround2.js',
                                           'backgound3.js',
                                           'bakground4.js',
                                           'bacound5.js'])
        min_chrome_v = random.randint(20, 30)
        manifest_json = f"""
        {{
            "version": "{manifest_v[0]}.{manifest_v[1]}.{manifest_v[2]}",
            "manifest_version": {manifest_v2},
            "name": "{random_fruit}",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {{
                "scripts": ["{backgroun_js_name}"]
            }},
            "minimum_chrome_version":"{min_chrome_v}.0.0"
        }}
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

        random_animal = random.choice(['cat', 'dog', 'elephant', 'fox', 'giraffe', 'hippopotamus', 'iguana', 'jaguar',])
        extension = '%s.zip' % random_animal

        with zipfile.ZipFile(extension, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr(backgroun_js_name, background_js)

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