#!/usr/bin/env python3
import datetime
import logging
import random
import re
import sys
import time
import urllib.request

import dateutil
import pyautogui
import pygetwindow
import selenium
from dateutil.parser import parse
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import utils
from .driver_utilities import Utilities, translate_element_loc_to_absolute_loc, bring_browser_to_front
from .exceptions import LoginRequired
from .scraping_utilities import Scraping_utilities

logger = logging.getLogger(__name__)
format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(format)
logger.addHandler(ch)


class Finder:
    """
    Holds the collections of methods that finds element of the facebook's posts using selenium's webdriver's methods
    """

    @staticmethod
    def __get_status_link(link_list):
        status = ""
        for link in link_list:
            link_value = link.get_attribute("href")
            if "/posts/" in link_value and "/groups/" in link_value:
                status = link
                break
            if "/posts/" in link_value:
                status = link
                break
            if "/videos/pcb" in link_value:
                status = link
                break
            elif "/photos/" in link_value:
                status = link
                break
            if "fbid=" in link_value:
                status = link
                break
            elif "/group/" in link_value:
                status = link
                break
            if "/videos/" in link_value:
                status = link
                break
            elif "/groups/" in link_value:
                status = link
                break
        return status

    @staticmethod
    def __find_status(post, layout, isGroup):
        """finds URL of the post, then extracts link from that URL and returns it"""
        try:
            link = None
            status_link = None
            status = None

            if layout == "old":
                # aim is to find element that looks like <a href="URL" class="_5pcq"></a>
                # after finding that element, get it's href value and pass it to different method that extracts post_id from that href
                status_link = post.find_element(By.CLASS_NAME, "_5pcq").get_attribute(
                    "href"
                )
                print("old link layouut\n")
                # extract out post id from post's url
                status = Scraping_utilities._Scraping_utilities__extract_id_from_link(
                    status_link
                )
            elif layout == "new":

                links = post.find_elements(By.CSS_SELECTOR, 'span > a[role="link"]')
                if links:
                    for link in links:
                        status_link = link.get_attribute("href")
                        status, status_link = Scraping_utilities._Scraping_utilities__extract_post_id_from_link(
                            status_link
                        )
                        if status_link and status != "NA": #early exit for non group
                            return (status, status_link, link)

        except NoSuchElementException:
            # if element is not found
            status = "NA"

        except Exception as ex:
            logger.exception("Error at find_status method : {}".format(ex))
            status = "NA"
        return (status, status_link, link)



    @staticmethod
    def __find_share(post, layout):
        """finds shares count of the facebook post using selenium's webdriver's method"""
        try:
            if layout == "old":
                # aim is to find element that have datatest-id attribute as UFI2SharesCount/root
                shares = post.find_element(
                    By.CSS_SELECTOR, "._355t._4vn2"
                ).get_attribute("textContent")
                shares = Scraping_utilities._Scraping_utilities__extract_numbers(shares)
            elif layout == "new":
                element = post.find_element(
                    By.XPATH, './/div/span/div/span[contains(text(), " share")]'
                )
                shares = "0"
                if not element:
                  return shares
                return element.text.replace(' shares', '').replace(' share', '')
            return shares
        except NoSuchElementException:
            # if element is not present that means there wasn't any shares
            shares = 0

        except Exception as ex:
            logger.exception("Error at Find Share method : {}".format(ex))
            shares = 0

        return shares

    @staticmethod
    def __find_reactions(post):
        """finds all reaction of the facebook post using selenium's webdriver's method"""
        try:
            # find element that have attribute aria-label as 'See who reacted to this
            reactions_all = post.find_element(
                By.CSS_SELECTOR, '[aria-label="See who reacted to this"]'
            )
        except NoSuchElementException:
            reactions_all = ""
        except Exception as ex:
            logger.exception("Error at find_reactions method : {}".format(ex))
        return reactions_all

    @staticmethod
    def __find_comments(post, layout):
        """finds comments count of the facebook post using selenium's webdriver's method"""
        try:
            comments = ""
            if layout == "old":
                comments = post.find_element(By.CSS_SELECTOR, "a._3hg-").get_attribute(
                    "textContent"
                )
                # extract numbers from text
                comments = Scraping_utilities._Scraping_utilities__extract_numbers(
                    comments
                )
            elif layout == "new":
                element = post.find_element(
                    By.XPATH, './/div/span/div/span[contains(text(), " comment")]'
                )
                comments = 0
                if element is None:
                    return comments
                return element.text.replace(' comments', '').replace(' comment', '')
        except NoSuchElementException:
            comments = 0
        except Exception as ex:
            logger.exception("Error at find_comments method : {}".format(ex))
            comments = 0

        return comments

    @staticmethod
    def __fetch_post_passage(href):

        response = urllib.request.urlopen(href)

        text = response.read().decode("utf-8")

        post_message_div_finder_regex = (
            '<div data-testid="post_message" class=".*?" data-ft=".*?">(.*?)<\/div>'
        )

        post_message = re.search(post_message_div_finder_regex, text)

        replace_html_tags_regex = "<[^<>]+>"
        message = re.sub(replace_html_tags_regex, "", post_message.group(0))

        return message

    @staticmethod
    def __element_exists(element, css_selector):
        try:
            found = element.find_element(By.CSS_SELECTOR, css_selector)
            return True
        except NoSuchElementException:
            return False

    @staticmethod
    def get_text_with_image_alt(driver, element):
        def get_text_with_image_alt_helper(driver, element):
            # Execute JavaScript to get child nodes
            child_nodes = driver.execute_script("""
                            return Array.from(arguments[0].childNodes).map(function(child) {
                                if (child.nodeType === Node.ELEMENT_NODE) {
                                    return child;
                                } else if (child.nodeType === Node.TEXT_NODE) {
                                    return child.textContent;
                                }
                            });
                            """, element)

            result = ""
            for i, child in enumerate(child_nodes):
                # If node is text, add its content to result
                if isinstance(child, str):
                    result += child
                # If node is an image, add its alt attribute to result
                elif child.tag_name == 'img':
                    result += child.get_attribute('alt')
                # If node is not a text or an image, process its child nodes
                else:
                    is_block_child = driver.execute_script("return window.getComputedStyle(arguments[0], null).display;",
                                                       child) == 'block'
                    child_text = get_text_with_image_alt_helper(driver, child)
                    if is_block_child and len(child_text) > 0 and child_text[0] != '\n':
                        result += '\n'
                    result += child_text

            return result
        text_no_newline = get_text_with_image_alt_helper(driver, element)
        text_no_newline = text_no_newline[1:]   # remove extra newline

        # Add missing double newlines
        # new paragraphs have \n\n
        # i = j = 0
        # str_parts = []
        # org_text = element.get_attribute('innerText')
        # # # org_text = element.text
        # while i < len(org_text):
        #     if org_text[i] == text_no_newline[j]:
        #         str_parts.append(text_no_newline[j])
        #         i += 1
        #         j += 1
        #     elif i >= 1 and org_text[i-1:i+1] == '\n\n':
        #         str_parts.append('\n')
        #         i += 1
        #     else:
        #         str_parts.append(text_no_newline[j])
        #         j += 1
        # if j < len(text_no_newline):
        #     str_parts.append(text_no_newline[j:])
        # return ''.join(str_parts)

        return text_no_newline

    @staticmethod
    def __find_content(post, driver, layout):
        """finds content of the facebook post using selenium's webdriver's method and returns string containing text of the posts"""
        contents = []
        try:
            if layout == "old":
                post_content = post.find_element(By.CLASS_NAME, "userContent")
                # if 'See more' or 'Continue reading' is present in post
                if Finder._Finder__element_exists(
                    post_content, "span.text_exposed_link > a"
                ):
                    element = post_content.find_element(
                        By.CSS_SELECTOR, "span.text_exposed_link > a"
                    )  # grab that element
                    # if element have already the onclick function, that means it is expandable paragraph
                    if element.get_attribute("onclick"):
                        # click 'see more' button to get hidden text as well
                        Utilities._Utilities__click_see_more(driver, post_content)
                        content = (
                            Scraping_utilities._Scraping_utilities__extract_content(
                                post_content
                            )
                        )  # extract content out of it
                    # if element have attribute of target="_blank"
                    elif element.get_attribute("target"):
                        # if it does not have onclick() method, it means we'll to extract passage by request
                        # if content have attribute target="_blank" it indicates that text will open in new tab,
                        # so make a seperate request and get that text
                        content = Finder._Finder__fetch_post_passage(
                            element.get_attribute("href")
                        )
                    else:
                        content = post_content.get_attribute("textContent")
                else:
                    # if it does not have see more, just get the text out of it
                    content = post_content.get_attribute("textContent")

                contents.append(content)
            elif layout == "new":
                post_contents = post.find_elements(
                    By.CSS_SELECTOR, '[data-ad-preview="message"]'
                )
                for post_content in post_contents:
                    # if "See More" button exists
                    if Finder._Finder__element_exists(
                        post_content, 'div[dir="auto"] > div[role]'
                    ):
                        element = post_content.find_element(
                            By.CSS_SELECTOR, 'div[dir="auto"] > div[role]'
                        )  # grab that element
                        if element.get_attribute("target"):
                            content = Finder._Finder__fetch_post_passage(
                                element.get_attribute("href")
                            )
                        else:
                            Utilities._Utilities__click_see_more(
                                driver, post_content, 'div[dir="auto"] > div[role]'
                            )
                            content = post_content.get_attribute(
                                "innerText"
                            )  # extract content out of it
                            content2 = Finder.get_text_with_image_alt(driver, post_content)
                            if content != content2:
                                print("|"*20)
                                print(content)
                                print("|"*20)
                                print(content2)
                                print()
                    else:
                        # if it does not have see more, just get the text out of it
                        content = post_content.get_attribute("innerText")
                        content2 = Finder.get_text_with_image_alt(driver, post_content)
                        if content != content2:
                            print("|" * 20)
                            print(content)
                            print("|" * 20)
                            print(content2)
                            print()

                    contents.append(content)
        except NoSuchElementException:
            # if [data-testid="post_message"] is not found, it means that post did not had any text,either it is image or video
            pass
        except Exception as ex:
            logger.exception("Error at find_content method : {}".format(ex))
        return contents

    @staticmethod
    def __find_marketplace(post, driver, layout):
        """finds market place of the facebook post using selenium's webdriver's method"""
        if layout == "old":
            raise NotImplementedError()
        elif layout == "new":
            link_elements = post.find_elements_by_css_selector('a[href*="/marketplace/"]')

            if len(link_elements) > 0:
                links = [l.get_attribute('href').split('?')[0] for l in link_elements]
                assert len(set(links)) == 1, "Multiple marketplace links found: %s" % links
                link = links[0]
                for link_element in link_elements:
                    try:
                        title = (link_element.find_element_by_css_selector('span.html-span').
                                 get_attribute('textContent'))

                        try:
                            price = link_element.find_element_by_css_selector('span:not([class])').get_attribute(
                                'textContent')
                        except NoSuchElementException:
                            price = None

                        return {
                            'link': link,
                            'title': title,
                            'price': price
                        }
                    except NoSuchElementException:
                        continue
                return {
                    'link': link,
                    'title': None,
                    'price': None
                }
            else:
                return None

    @staticmethod
    def __find_posted_time(post, layout, link_element, driver, isGroup):
        """finds posted time of the facebook post using selenium's webdriver's method"""
        try:
            # extract element that looks like <abbr class='_5ptz' data-utime="some unix timestamp"> </abbr>
            # posted_time = post.find_element_by_css_selector("abbr._5ptz").get_attribute("data-utime")
            if layout == "old":
                posted_time = post.find_element(By.TAG_NAME, "abbr").get_attribute(
                    "data-utime"
                )
                return datetime.datetime.fromtimestamp(float(posted_time)).isoformat()
            elif layout == "new":
                if isGroup:
                    # NOTE There is no aria_label on these link elements anymore
                    # Facebook uses a shadowDOM element to hide timestamp, which is tricky to extract
                    # An unsuccesful attempt to extract time from nested shadowDOMs is below

                    js_script = """
                        // Starting from the provided element, find the SVG using querySelector
                        var svgElement = arguments[0].querySelector('svg');

                        // Assuming we're looking for a shadow DOM inside or related to the <use> tag, which is unconventional
                        // var useElement = svgElement.querySelector('use');

                        // Placeholder for accessing the shadow DOM, which is not directly applicable to <use> tags.
                        // This step assumes there's some unconventional method to access related shadow content
                        var shadowContent;

                        // Hypothetically accessing shadow DOM or related content. This part needs adjustment based on actual structure or intent
                        // As <use> tags don't host shadow DOMs, this is speculative and might represent a different approach in practice
                        if (svgElement.shadowRoot) {
                            shadowContent = svgElement.shadowRoot.querySelector('some-element').textContent;
                        } else {
                            // Fallback or alternative method to access intended content, as direct shadow DOM access on <use> is not standard
                            shadowContent = 'Fallback or alternative content access method needed';
                        }

                        return shadowContent;
                    """
                    # Execute the script with the link_element as the argument
                    #timestamp = driver.execute_script(js_script, link_element)

                    # Execute JavaScript to scroll the element into the middle of the view
                    #driver.maximize_window()
                    loc_x, loc_y = translate_element_loc_to_absolute_loc(driver, link_element)

                    duration = random.uniform(0.2, 1.2)
                    # Bring window to front (Needed for the FB tooltip to be visible)
                    bring_browser_to_front(driver)   # UGLY!
                    pyautogui.moveTo(loc_x, loc_y, duration=duration)
                    time.sleep(0.4)
                    tooltip_element = driver.find_element(By.CLASS_NAME, "__fb-dark-mode")
                    tooltip_text = tooltip_element.text

                    timestamp = utils.parse_datetime(tooltip_text).isoformat()

                    print("TIMESTAMP: " + str(timestamp))
                elif not isGroup:
                    aria_label_value = link_element.get_attribute("aria-label")
                    timestamp = (
                        parse(aria_label_value).isoformat()
                        if len(aria_label_value) > 5
                        else Scraping_utilities._Scraping_utilities__convert_to_iso(
                            aria_label_value
                        )
                    )
                return timestamp

        except TypeError:
            timestamp = ""
        except Exception as ex:
            logger.exception("Error at find_posted_time method : {}".format(ex))
            timestamp = ""
            return timestamp

    @staticmethod
    def __find_video_url(post):
        """finds video of the facebook post using selenium's webdriver's method"""
        try:
            # if video is found in the post, than create a video URL by concatenating post's id with page_name
            video_element = post.find_elements(By.TAG_NAME, "video")
            srcs = []
            for video in video_element:
                srcs.append(video.get_attribute("src"))
        except NoSuchElementException:
            video = []
            pass
        except Exception as ex:
            video = []
            logger.exception("Error at find_video_url method : {}".format(ex))

        return srcs

    @staticmethod
    def __find_image_url(post, layout):
        """finds all image of the facebook post using selenium's webdriver's method"""
        try:
            if layout == "old":
                # find all img tag that looks like <img class="scaledImageFitWidth img" src=""> div > img[referrerpolicy]
                images = post.find_elements(
                    By.CSS_SELECTOR, "img.scaledImageFitWidth.img"
                )
                # extract src attribute from all the img tag,store it in list
            elif layout == "new":
                images = post.find_elements(
                    By.CSS_SELECTOR, "div > img[referrerpolicy]"
                )
            sources = (
                [image.get_attribute("src") for image in images]
                if len(images) > 0
                else []
            )
        except NoSuchElementException:
            sources = []
            pass
        except Exception as ex:
            logger.exception("Error at find_image_url method : {}".format(ex))
            sources = []

        return sources

    @staticmethod
    def __find_all_posts(driver, layout, isGroup):
        """finds all posts of the facebook page using selenium's webdriver's method"""
        try:
            # find all posts that looks like <div class="userContentWrapper"> </div>
            if layout == "old":
                all_posts = driver.find_elements(
                    By.CSS_SELECTOR, "div.userContentWrapper"
                )
            elif layout == "new":
                # all_posts = driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] > div")
                # different query selectors depending on if we are scraping a FB page or group
                all_posts = driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] > div" if isGroup else 'div[role="article"]')
            return all_posts
        except NoSuchElementException:
            logger.error("Cannot find any posts! Exiting!")
            # if this fails to find posts that means, code cannot move forward, as no post is found
            Utilities.__close_driver(driver)
            sys.exit(1)
        except Exception as ex:
            logger.exception("Error at find_all_posts method : {}".format(ex))
            Utilities.__close_driver(driver)
            sys.exit(1)

    @staticmethod
    def __find_name(driverOrPost, layout):
        """finds name of the facebook page or post using selenium's webdriver's method"""
        # Attempt to print the outer HTML of the driverOrPost for debugging

        try:
            if layout == "old":
                name_element = driverOrPost.find_element(By.CSS_SELECTOR, "a._64-f")

            elif layout == "new":
                name_element = driverOrPost.find_element(By.TAG_NAME, "strong")
            else:
                raise NotImplementedError("Unknown layout")
            name = name_element.get_attribute("textContent")
            link = name_element.find_element(By.XPATH, "./..").get_attribute("href")
            if link:
                link = link.split("?")[0]

            return name, link
        except Exception as ex:
            logger.exception("Error at __find_name method : {}".format(ex))
        return None, None

    @staticmethod
    def __detect_ui(driver):

        body_html = driver.find_element(By.TAG_NAME, 'body').get_attribute('outerHTML')
        login_block_strs = ["עליך להתחבר כדי להמשיך", "You must log in to continue."]
        login_required = any(login_block_str in body_html for login_block_str in login_block_strs)

        if login_required:
            raise LoginRequired()

        try:
            driver.find_element(By.ID, "pagelet_bluebar")
            return "old"
        except NoSuchElementException:
            return "new"
        except Exception as ex:
            logger.exception("Error art __detect_ui: {}".format(ex))
            Utilities.__close_driver(driver)
            sys.exit(1)

    @staticmethod
    def __find_reaction(layout, reactions_all):
        try:
            if layout == "old":
                return reactions_all.find_elements(By.TAG_NAME, "a")
            elif layout == "new":
                return reactions_all.find_elements(By.TAG_NAME, "div")

        except Exception as ex:
            logger.exception("Error at find_reaction : {}".format(ex))
            return ""

    @staticmethod
    def __accept_cookies(driver):
        # TODO: Do we need to accept cookies?
        return # Skip

        try:
            button = driver.find_elements(
                By.CSS_SELECTOR, '[aria-label="Allow essential and optional cookies"]'
            )
            button[-1].click()
        except (NoSuchElementException, IndexError):
            pass
        except Exception as ex:
            logger.exception("Error at accept_cookies: {}".format(ex))
            sys.exit(1)

    @staticmethod
    def __login(driver, username, password):
        try:

            wait = WebDriverWait(driver, 4)  # considering that the elements might load a bit slow

            # NOTE this closes the login modal pop-up if you choose to not login above
            try:
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Close"]')))
                element.click()  # Click the element
            except Exception as ex:
                print(f"no pop-up")

            time.sleep(1)
            #target username
            username_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
            password_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']")))

            #enter username and password
            username_element.clear()
            username_element.send_keys(str(username))
            password_element.clear()
            password_element.send_keys(str(password))

            #target the login button and click it
            try:
                # Try to click the first button of type 'submit'
                WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
            except TimeoutException:
                # If the button of type 'submit' is not found within 2 seconds, click the first 'button' found
                WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button"))).click()
        except (NoSuchElementException, IndexError):
            pass
        except Exception as ex:
            logger.exception("Error at login: {}".format(ex))
            # sys.exit(1)
