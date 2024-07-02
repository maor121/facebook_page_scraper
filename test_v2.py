import time

import facebook_page_scraper
from facebook_page_scraper.exceptions import LoginRequired, TemporarilyBanned
from facebook_page_scraper.browser_ext import ProxyAuthChromeExtension, HttpStatusExtention


def retry_wrapper(func, retry_count=3, sleep_time=3):
    for i in range(retry_count):
        try:
            if i > 0:
                print(f"Retry {i}...")
            return func()
        except LoginRequired:
            print("LoginRequired")
            time.sleep(sleep_time)
        except TemporarilyBanned:
            print("TemporarilyBanned")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(sleep_time)
    return None


if __name__ == "__main__":

    proxy_username = "USERNAME"

    proxy_password = "PASSWORD"
    endpoint = 'PROXY_URL'

    proxy_port = 99999   # YOUR PROXY
    proxy_extension = ProxyAuthChromeExtension(proxy_username, proxy_password, endpoint, proxy_port)
    http_status_ext = HttpStatusExtention()

    group_id = 441654752934426  # problematic realestate group
    #group_id = 170918513059147  # anime group (test)

    MAX_RETRIES = 2
    timings = []
    for group_id in (441654752934426, 295395253832427, 527528920661747, 692882024975122):
        scrape_start = time.time()
        print("Scraping group:", group_id)

        group = facebook_page_scraper.Facebook_scraper(f"{group_id}", max_days_back=2,
                                                       max_hit_back_count=2,
                                                       browser="chrome",
                                                       isGroup=True,  headless=False, extensions=[proxy_extension,
                                                                                                  http_status_ext],
                                                       #browser_args=["--incognito"]
                                                       browser_args=["--lang=he"],
                                                       browser_exp_options={
                                                           # disalbe image loading
                                                           "prefs": {"profile.managed_default_content_settings.images": 2},
                                                           #"mobileEmulation": {"deviceName": "iPad Mini"}
                                                       })
        res_json = retry_wrapper(group.scrap_to_json, retry_count=MAX_RETRIES)
        print(res_json)
        scrape_end = time.time()
        timings.append(scrape_end - scrape_start)
        print("---")

    print("Timings:", timings)
    print("Average time:", sum(timings) / len(timings))
    print("Done")