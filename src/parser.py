import logging
import requests
from lxml import html

logger = logging.getLogger(__name__)

def _parse_episodes(episode_ranges):
    """Parses episode ranges into a list of episode numbers"""
    episodes = []
    for text in episode_ranges:
        if "-" in text:
            try:
                start, end = map(int, text.split("-"))
                episodes.extend(range(start, end + 1))
            except ValueError:
                logger.warning(f"Could not parse range: {text}")
        else:
            try:
                episodes.append(int(text))
            except ValueError:
                logger.warning(f"Could not parse episode number: {text}")
    return episodes

def get_episode_status(url: str) -> dict[str, list[int]]:
    """
    Fetches and parses episode statuses from an animefillerlist.com URL

    Returns a dictionary with status names as keys and lists of episode numbers as values
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = html.fromstring(response.content)

        statuses = {}

        # XPath for different categories
        xpaths = {
            "MangaCanon": '//div[contains(@class, "manga_canon")]//span[@class="Episodes"]/a/text()',
            "Mixed": '//div[contains(@class, "mixed_canon/filler")]//span[@class="Episodes"]/a/text()',
            "Filler": '//div[contains(@class, "filler") and not(contains(@class, "mixed_canon/filler"))]//span[@class="Episodes"]/a/text()',
            "AnimeCanon": '//div[contains(@class, "anime_canon")]//span[@class="Episodes"]/a/text()',
        }

        for status_name, xpath in xpaths.items():
            episode_ranges = data.xpath(xpath)
            if episode_ranges:
                logging.debug(f"Found ranges for '{status_name}': {episode_ranges}")
                statuses[status_name] = _parse_episodes(episode_ranges)

        return statuses

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return {}