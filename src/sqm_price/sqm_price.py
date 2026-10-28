import random

import requests
from bs4 import BeautifulSoup

from src.app_logging import get_logger
from src.proxies.proxies import as_requests_proxies, fetch_and_cache_proxies

logger = get_logger(__name__)

URL = "https://www.imoti.net/bg/sredni-ceni"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept-Language": "bg-BG,bg;q=0.9,en;q=0.8",
}
MAX_ATTEMPTS = 15


def _get_page() -> requests.Response | None:
    """Try random proxies until one returns the price table."""
    proxies = fetch_and_cache_proxies()
    for proxy in random.sample(proxies, k=min(MAX_ATTEMPTS, len(proxies))):
        try:
            r = requests.get(
                URL, headers=HEADERS, proxies=as_requests_proxies(proxy), timeout=8
            )
            r.raise_for_status()
            if "<tbody" in r.text:
                logger.info("Fetched page via %s", proxy)
                return r
            logger.warning("No table via %s", proxy)
        except requests.RequestException as exc:
            logger.warning("Proxy %s failed: %s", proxy, type(exc).__name__)
    return None


def fetch_avg_sqm_price_eur() -> dict[str, float] | dict[str, str]:
    """Scrape the average residential price per square meter in EUR."""
    response = _get_page()
    if response is None:
        logger.error("All %d proxy attempts failed", MAX_ATTEMPTS)
        return {"error": "Failed to fetch sqm price"}

    try:
        rows = (
            BeautifulSoup(response.content, "html.parser").find("tbody").find_all("tr")
        )

        prices = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) > 1:
                text = (
                    cells[1].get_text(strip=True).replace("\xa0", "").replace(" ", "")
                )
                try:
                    prices.append(float(text.replace(",", ".")))
                except ValueError:
                    continue

        avg_price = sum(prices) / len(prices) if prices else None
        logger.info("Computed average EUR price per sqm: %s", avg_price)
        return {"avg_price": avg_price}

    except Exception:
        logger.exception("Failed to parse sqm price")
        return {"error": "Failed to fetch sqm price"}
