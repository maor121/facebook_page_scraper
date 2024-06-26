import time

import facebook_page_scraper
from facebook_page_scraper.proxy_ext import ProxyAuthChromeExtension

if __name__ == "__main__":

    proxy_username = "USERNAME"

    proxy_password = "PASSWORD"
    endpoint = 'PROXY_URL'

    proxy_port = 99999   # YOUR PROXY
    proxy_extension = ProxyAuthChromeExtension(proxy_username, proxy_password, endpoint, proxy_port)

    group_id = 441654752934426  # problematic realestate group
    #group_id = 170918513059147  # anime group (test)

    group = facebook_page_scraper.Facebook_scraper(f"{group_id}",40,"chrome",
                                                   isGroup=True,  headless=False, extensions=[proxy_extension],
                                                   #browser_args=["--incognito"]
                                                   browser_args=["--lang=he"],
                                                   browser_exp_options={
                                                       "prefs": {"profile.managed_default_content_settings.images": 2}})
    res = group.scrap_to_json()
    print(res)
