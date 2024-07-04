#!/usr/bin/env python3

import logging
import random
import time
from random import randint

import pygetwindow
from selenium.common.exceptions import (NoSuchElementException,
                                        WebDriverException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from facebook_page_scraper.exceptions import TemporarilyBanned

logger = logging.getLogger(__name__)
format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(format)
logger.addHandler(ch)


def bring_browser_to_front(driver):
    # Execute JavaScript to check if the current page is visible

    # Get the title of the current window
    #window_handle = driver.current_window_handle
    window_title = driver.title
    window = pygetwindow.getWindowsWithTitle(window_title)[0]

    try:
        if window.isMinimized:
            window.restore()
        if not window.isActive:
            window.activate()
    except pygetwindow.PyGetWindowException as ex:
        # logger.exception("Error at bring_browser_to_front: {}".format(ex))
        pass    # sometimes the browser is at the front, but we recieve exception anyway, continue

    # Bring to front (by minimizing & maximizing)
    # position = driver.get_window_position()
    # driver.minimize_window()
    # driver.set_window_position(position['x'], position['y'])


def translate_element_loc_to_absolute_loc(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    win_pos = driver.get_window_position()
    el_pos = element.location
    scroll_x = driver.execute_script('return window.scrollX;')
    scroll_y = driver.execute_script('return window.scrollY;')
    panel_height = driver.execute_script('return window.outerHeight - window.innerHeight;')
    delta_x = random.randint(15,22)

    return win_pos['x'] + el_pos['x'] - scroll_x + delta_x, win_pos['y'] + el_pos['y'] - scroll_y + panel_height


class Utilities:

    @staticmethod
    def __close_driver(driver):
        """expects driver's instance, closes the driver"""
        try:
            driver.close()
            driver.quit()
        except Exception as ex:
            logger.exception("Error at close_driver method : {}".format(ex))

    @staticmethod
    def __close_error_popup(driver):
        '''expects driver's instance as a argument and checks if error shows up
        like "We could not process your request. Please try again later" ,
        than click on close button to skip that popup.'''
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a.layerCancel')))  # wait for popup to show
            # grab that popup's close button
            button = driver.find_element(By.CSS_SELECTOR, "a.layerCancel")
            button.click()  # click "close" button
        except WebDriverException:
            # it is possible that even after waiting for given amount of time,modal may not appear
            pass
        except NoSuchElementException:
            pass  # passing this error silently because it may happen that popup never shows up

        except Exception as ex:
            # if any other error occured except the above one
            logger.exception(
                "Error at close_error_popup method : {}".format(ex))

    @staticmethod
    def __scroll_down_half(driver):
        try:
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight / 2);")
        except Exception as ex:
            # if any error occured than close the driver and exit
            Utilities.__close_driver(driver)
            logger.exception(
                "Error at scroll_down_half method : {}".format(ex))

    @staticmethod
    def __close_modern_layout_signup_modal(driver):
        BLOCKED_POPUP_COUNT = 4

        popup_count = 0
        try:
            found_popup = True
            while found_popup:
                # driver.execute_script(
                #     "window.scrollTo(0, document.body.scrollHeight);")
                close_text_options = ["Close", "סגירה"]
                found_popup = False
                for text in close_text_options:
                    try:
                        close_button = driver.find_element(
                            By.CSS_SELECTOR, f'[aria-label="{text}"]')

                        found_popup = True
                        popup_count += 1

                        if popup_count == BLOCKED_POPUP_COUNT:
                            raise TemporarilyBanned()

                        # bring_browser_to_front(driver)
                        # loc_x, loc_y = translate_element_loc_to_absolute_loc(driver, close_button)
                        # duration = random.uniform(0.2, 1.2)
                        # pyautogui.moveTo(loc_x, loc_y, duration=duration)
                        # pyautogui.click()

                        close_button.click()
                        break
                    except NoSuchElementException as ex:
                        pass
                if found_popup:
                    time.sleep(1)
                    # try again
        except TemporarilyBanned as e:
            raise e
        except Exception as ex:
            logger.exception(
                "Error at close_modern_layout_signup_modal: {}".format(ex))

    @staticmethod
    def __scroll_down(driver, layout):
        """expects driver's instance as a argument, and it scrolls down page to the most bottom till the height"""
        try:
            if layout == "old":
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
            elif layout == "new":
                body = driver.find_element(By.CSS_SELECTOR, "body")
                for _ in range(randint(1, 3)):
                    body.send_keys(Keys.PAGE_UP)
                time.sleep(randint(5, 6))
                for _ in range(randint(5, 8)):
                    body.send_keys(Keys.PAGE_DOWN)
                #driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                # Utilities.__close_modern_layout_signup_modal(driver)
        except Exception as ex:
            # if any error occured than close the driver and exit
            Utilities.__close_driver(driver)
            logger.exception("Error at scroll_down method : {}".format(ex))

    @staticmethod
    def __close_popup(driver):
        """expects driver's instance and closes modal that ask for login, by clicking "Not Now" button """
        try:
            # Utilities.__scroll_down_half(driver)  #try to scroll
            # wait for popup to show
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.ID, 'expanding_cta_close_button')))
            # grab "Not Now" button
            popup_close_button = driver.find_element(
                By.ID, 'expanding_cta_close_button')
            popup_close_button.click()  # click the button
        except WebDriverException:
            # modal may not popup, so no need to raise exception in case it is not found
            pass
        except NoSuchElementException:
            pass  # passing this exception silently as modal may not show up
        except Exception as ex:
            logger.exception("Error at close_popup method : {}".format(ex))

    @staticmethod
    def __wait_for_element_to_appear(driver, layout, timeout):
        """expects driver's instance, wait for posts to show.
        post's CSS class name is userContentWrapper
        """
        try:
            if layout == "old":
                # wait for page to load so posts are visible
                body = driver.find_element(By.CSS_SELECTOR, "body")
                for _ in range(randint(3, 5)):
                    body.send_keys(Keys.PAGE_DOWN)
                WebDriverWait(driver, timeout).until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.userContentWrapper')))
                return True
            elif layout == "new":
                try:
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-posinset]")))
                except TimeoutError:
                    logger.info("ugly fix for other user agents")
                    WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']")))
                    time.sleep(2)
                print("new layout loaded")

                return True

        except WebDriverException:
            # if it was not found,it means either page is not loading or it does not exists
            logger.critical("No posts were found!")
            return False
            # (optional) exit the program, because if posts does not exists,we cannot go further
            # Utilities.__close_driver(driver)
            # sys.exit(1)
        except Exception as ex:
            logger.exception(
                "Error at wait_for_element_to_appear method : {}".format(ex))
            return False
            # Utilities.__close_driver(driver)

    @staticmethod
    def __click_see_more(driver, content, selector=None):
        """expects driver's instance and selenium element, click on "see more" link to open hidden content"""
        try:
            if not selector:
                # find element and click 'see more' button
                element = content.find_element(
                    By.CSS_SELECTOR, 'span.see_more_link_inner')
            else:
                element = content.find_element(By.CSS_SELECTOR,
                                               selector)
            # click button using js
            driver.execute_script("arguments[0].click();", element)

        except NoSuchElementException:
            # if it doesn't exists than no need to raise any error
            pass
        except AttributeError:
            pass
        except IndexError:
            pass
        except Exception as ex:
            logger.exception("Error at click_see_more method : {}".format(ex))

    @staticmethod
    def __close_cookie_consent_modern_layout(driver):
        # To avoid the cookie consent prompt
        try:
          allow_span = driver.find_element(
             By.XPATH, '//div[contains(@aria-label, "Allow")]/../following-sibling::div')
          allow_span.click()
        except Exception as ex:
            logger.debug('The Cookie Consent Prompt was not found!: ', ex)
            try:
                driver.find_element(By.XPATH, '//span[contains(text(), "דחיית קובצי Cookie")]').click()
            except Exception as ex2:
                #if not found, that's fine silently just log thing do not stop
                logger.debug('The Cookie Consent Prompt was not found!: ', ex2)

