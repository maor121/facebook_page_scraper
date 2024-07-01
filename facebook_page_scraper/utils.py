"""
Copied from facebook_scraper repo
remove some functions
"""
import re
from datetime import datetime, timedelta
import calendar
from typing import Optional

import dateparser
import logging

logger = logging.getLogger(__name__)


def find_and_search(node, selector, pattern, cast=str):
    container = node.find(selector, first=True)
    match = container and pattern.search(container.html)
    return match and cast(match.groups()[0])


def parse_int(value: str) -> int:
    return int(''.join(filter(lambda c: c.isdigit(), value)))


def parse_duration(s) -> int:
    match = re.search(r'T(?P<hours>\d+H)?(?P<minutes>\d+M)?(?P<seconds>\d+S)', s)
    if match:
        result = 0
        for k, v in match.groupdict().items():
            if v:
                if k == 'hours':
                    result += int(v.strip("H")) * 60 * 60
                elif k == "minutes":
                    result += int(v.strip("M")) * 60
                elif k == "seconds":
                    result += int(v.strip("S"))
        return result


def remove_control_characters(html):
    # type: (t.Text) -> t.Text
    """
    Strip invalid XML characters that `lxml` cannot parse.
    """
    # See: https://github.com/html5lib/html5lib-python/issues/96
    #
    # The XML 1.0 spec defines the valid character range as:
    # Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
    #
    # We can instead match the invalid characters by inverting that range into:
    # InvalidChar ::= #xb | #xc | #xFFFE | #xFFFF | [#x0-#x8] | [#xe-#x1F] | [#xD800-#xDFFF]
    #
    # Sources:
    # https://www.w3.org/TR/REC-xml/#charsets,
    # https://lsimons.wordpress.com/2011/03/17/stripping-illegal-characters-out-of-xml-in-python/
    def strip_illegal_xml_characters(s, default, base=10):
        # Compare the "invalid XML character range" numerically
        n = int(s, base)
        if (
            n in (0xB, 0xC, 0xFFFE, 0xFFFF)
            or 0x0 <= n <= 0x8
            or 0xE <= n <= 0x1F
            or 0xD800 <= n <= 0xDFFF
        ):
            return ""
        return default

    # We encode all non-ascii characters to XML char-refs, so for example "💖" becomes: "&#x1F496;"
    # Otherwise we'd remove emojis by mistake on narrow-unicode builds of Python
    html = html.encode("ascii", "xmlcharrefreplace").decode("utf-8")
    html = re.sub(
        r"&#(\d+);?", lambda c: strip_illegal_xml_characters(c.group(1), c.group(0)), html
    )
    html = re.sub(
        r"&#[xX]([0-9a-fA-F]+);?",
        lambda c: strip_illegal_xml_characters(c.group(1), c.group(0), base=16),
        html,
    )
    # A regex matching the "invalid XML character range"
    html = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]").sub("", html)
    return html


month = (
    r"Jan(?:uary)?|"
    r"Feb(?:ruary)?|"
    r"Mar(?:ch)?|"
    r"Apr(?:il)?|"
    r"May|"
    r"Jun(?:e)?|"
    r"Jul(?:y)?|"
    r"Aug(?:ust)?|"
    r"Sep(?:tember)?|"
    r"Oct(?:ober)?|"
    r"Nov(?:ember)?|"
    r"Dec(?:ember)?"
)
day_of_week = r"Mon|" r"Tue|" r"Wed|" r"Thu|" r"Fri|" r"Sat|" r"Sun"
day_of_month = r"\d{1,2}"
specific_date_md = f"(?:{month}) {day_of_month}" + r"(?:,? \d{4})?"
specific_date_dm = f"{day_of_month} (?:{month})" + r"(?:,? \d{4})?"

date = f"{specific_date_md}|{specific_date_dm}|Today|Yesterday"

hour = r"\d{1,2}"
minute = r"\d{2}"
period = r"AM|PM|"

exact_time = f"(?:{date}) at {hour}:{minute} ?(?:{period})"
relative_time_years = r'\b\d{1,2} yr'
relative_time_months = r'\b\d{1,2} (?:mth|mo)'
relative_time_weeks = r'\b\d{1,2} wk'
relative_time_hours = r"\b\d{1,2} ?h(?:rs?)?"
relative_time_mins = r"\b\d{1,2} ?mins?"
relative_time = f"{relative_time_years}|{relative_time_months}|{relative_time_weeks}|{relative_time_hours}|{relative_time_mins}"

datetime_regex = re.compile(fr"({exact_time}|{relative_time})", re.IGNORECASE)
day_of_week_regex = re.compile(fr"({day_of_week})", re.IGNORECASE)


def parse_datetime(text: str, search=True) -> Optional[datetime]:
    """Looks for a string that looks like a date and parses it into a datetime object.

    Uses a regex to look for the date in the string.
    Uses dateparser to parse the date (not thread safe).

    Args:
        text: The text where the date should be.
        search: If false, skip the regex search and try to parse the complete string.

    Returns:
        The datetime object, or None if it couldn't find a date.
    """
    settings = {
        'RELATIVE_BASE': datetime.today().replace(minute=0, hour=0, second=0, microsecond=0)
    }
    if search:
        time_match = datetime_regex.search(text)
        dow_match = day_of_week_regex.search(text)
        if time_match:
            text = time_match.group(0).replace("mth", "month")
        elif dow_match:
            text = dow_match.group(0)
            today = calendar.day_abbr[datetime.today().weekday()]
            if text == today:
                # Fix for dateparser misinterpreting "last Monday" as today if today is Monday
                return dateparser.parse(text, settings=settings) - timedelta(days=7)

    text = text.replace("דקה אחת", "1 min").replace("דק'", "mins")
    result = dateparser.parse(text)   #, settings=settings)
    if result:
        return result.replace(microsecond=0)
    return None

