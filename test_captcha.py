import random
import time

import pyautogui
from selenium.webdriver.common.by import By

from facebook_page_scraper import Initializer
from facebook_page_scraper.driver_utilities import translate_element_loc_to_absolute_loc
from facebook_page_scraper.mouse_utils import MouseUtils


def test_captcha(url, button_func, response_func):
    driver = Initializer(
        "chrome", headless=False).init()

    try:
        driver.get(url)
        time.sleep(5)

        captcha_link = button_func(driver)

        duration = random.uniform(0.2, 1.2)

        loc_x, loc_y = translate_element_loc_to_absolute_loc(driver, captcha_link)
        #pyautogui.moveTo(loc_x + 30, loc_y, duration=duration)
        MouseUtils().move_to((loc_x + 30, loc_y), mouseSpeed="medium")
        # time.sleep(0.2)
        pyautogui.click()
        time.sleep(5)

        response = response_func(driver)
        print(response)
    finally:
        driver.close()
        driver.quit()


def test_captcha1():
    test_captcha( "https://recaptcha-demo.appspot.com/recaptcha-v3-request-scores.php",
                 lambda driver: driver.find_element(By.PARTIAL_LINK_TEXT, "Try again"),
                 lambda driver: driver.find_element(By.CLASS_NAME, "response").get_attribute("innerText"))


def test_captcha2():
    test_captcha("https://2captcha.com/demo/recaptcha-v3",
                 lambda driver: driver.find_element(By.XPATH, "//button[@type='submit']"),
                 lambda driver: driver.find_elements(By.XPATH, "//code")[0].get_attribute('innerText'))


if __name__ == "__main__":
    test_captcha2()
