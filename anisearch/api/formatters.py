# Attribution: https://github.com/IchBinLeoon/anisearch-discord-bot/blob/main/bot/anisearch/utils/formatters.py
import re
from datetime import datetime
from typing import Pattern

import html2text

HANDLE = html2text.HTML2Text(bodywidth=0)

HTML_TAG_REGEX: Pattern[str] = re.compile(r"\<.*?\>")


def format_birth_date(day: int, month: int) -> str:
    all_months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    suffixes = {1: "st", 2: "nd", 3: "rd"}
    value = "th" if 10 <= (day % 100) <= 20 else suffixes.get(day % 10, "th")
    return f"{day}{value} {all_months[month - 1]}"


def format_media_type(media_type: str) -> str:
    media_formats = {
        # Anime broadcast on television
        "TV": "TV",
        # Anime which are under 15 minutes in length and broadcast on television
        "TV_SHORT": "TV Short",
        # Anime movies with a theatrical release
        "MOVIE": "Movie",
        # Special episodes that have been included in DVD/Blu-ray releases,
        # picture dramas, pilots, etc
        "SPECIAL": "Special Episode",
        # Anime that have been released directly on DVD/Blu-ray without originally
        # going through a theatrical release or television broadcast
        # https://anime.stackexchange.com/q/16728
        "OVA": "OVA",
        # Anime that is originally released online or only available through streaming services.
        # https://anime.stackexchange.com/q/8500
        "ONA": "ONA",
        # Short anime released as a music video
        "MUSIC": "Short Music Video",
        # Professionally published manga with more than one chapter
        "MANGA": "Manga",
        # Written books released as a series of light novel
        "NOVEL": "Light Novel",
        # Manga with just one chapter; often called yomikiri (読み切り)
        "ONE_SHOT": "One-shot manga",
    }
    return media_formats.get(media_type, "Unknown")


def format_anime_status(media_status: str) -> str:
    anime_statuses = {
        "FINISHED": "Finished",
        "RELEASING": "Currently Airing",
        "NOT_YET_RELEASED": "Not Yet Aired",
        "CANCELLED": "Cancelled",
    }
    return anime_statuses.get(media_status, "Unknown")


def format_manga_status(media_status: str) -> str:
    manga_statuses = {
        "FINISHED": "Finished",
        "RELEASING": "Currently Publishing",
        "NOT_YET_RELEASED": "Not Yet Published",
        "CANCELLED": "Cancelled",
    }
    return manga_statuses.get(media_status, "Unknown")


def format_description(description: str, length: int = 4086) -> str:
    cleaned = HTML_TAG_REGEX.sub("", description)
    description = cleaned.replace("__", "**").replace("~!", "|| ").replace("!~", " ||")

    if len(description) > length:
        description = description[:length]
        if description.count("||") > 0 and (description.count("|") % 4) != 0:
            return f"{description} || …"
        return f"{description} …"

    return description


def format_date(day: int, month: int, year: int, style: str = 'D') -> str:
    datetime_obj = datetime(year=year, month=month, day=day)
    return f"<t:{int(datetime_obj.timestamp())}:{style}>"

