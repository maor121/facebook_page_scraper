import facebook_page_scraper
from facebook_page_scraper.proxy_ext import ProxyAuthChromeExtension

if __name__ == "__main__":

    proxy_username = "USERNAME"

    proxy_password = "PASSWORD"
    endpoint = 'PROXY_URL'

    proxy_port = 99999   # YOUR PROXY
    proxy_extension = ProxyAuthChromeExtension(proxy_username, proxy_password, endpoint, proxy_port)

    group = facebook_page_scraper.Facebook_scraper("170918513059147",5,"chrome",
                                                   isGroup=True,  headless=False, extensions=[proxy_extension])
    res = group.scrap_to_json()
    print(res)