import logging
import os, json
from typing import TYPE_CHECKING
from datetime import datetime
import requests
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from bs4.element import ResultSet

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s - %(message)s",
)
logger = logging.getLogger(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "proxies.json")

def load_cached_proxies() -> dict:
    """Read proxies from `proxies.json` if it's up-to-date; otherwise return empty.

    Returns an empty dict to signal that a refresh is needed when the stored
    date is older than today or the file doesn't exist yet.
    """
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        if data["Date"] < datetime.today().date().isoformat():
            logger.info("Proxies are stale and should be refreshed")
            return {}

        logger.info("Using cached proxies from %s", file_path)
        return data["proxies"]

    except FileNotFoundError:
        data = {
            "status": "OK",
            "try": 0,
            "date": datetime.today().date().isoformat(),
            "proxies": {},
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        logger.info("Created new proxies file at %s", file_path)

        return data["proxies"]


def  fetch_and_cache_proxies() -> None:
    """Fetch and persist a list of public HTTPS proxies.

    Downloads proxies, stores them in `proxies.json`, and refreshes only once
    per day. When up-to-date, reuses the cached proxies. This function writes
    the file and logs outcomes; it does not return a value.
    """
    url = "https://www.proxy-list.download/api/v1/get?type=https"

    old_proxies = load_cached_proxies()

    if not old_proxies:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            logger.info("Fetched proxy list successfully")

            # split the response
            lines = response.text.strip().split("\n")

            # create a dict with index
            proxies = {
                i + 1: f"https://{line.strip()}" for i, line in enumerate(lines) if line.strip()
            }

            data = {
                "status": "OK",
                "date": datetime.today().date().isoformat(),
                "proxies": proxies,
            }
            logger.info("Loaded %d proxies and prepared to save", len(proxies))
        except Exception:
            data = {
                "status": "Fail",
                "date": datetime.today().date().isoformat(),
                "proxies": old_proxies,
            }
            logger.exception("Failed to fetch proxies")
    else:
        data = {
            "Status": "OK",
            "Date": datetime.today().date().isoformat(),
            "proxies": old_proxies,
        }
        logger.info("Proxies are up-to-date; no refresh performed")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info("Saved proxies to %s", file_path)

