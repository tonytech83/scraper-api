import os
import json
import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from typing import Any
from src.app_logging import get_logger

from src.proxies.proxies import fetch_and_cache_proxies


logger = get_logger(__name__)

def fetch_avg_sqm_price_eur() -> dict[str, float] | dict[str, str]:
    """Scrape the average residential price per square meter in EUR.

    - Fetches `https://www.imoti.net/bg/sredni-ceni` and parses the table rows.
    - Computes the arithmetic mean of the values in the second column.

    Returns:
        {"avg_price": float} on success, or {"error": str} on failure.
    """
    # reload proxies data
    fetch_and_cache_proxies()


    base_dir = os.path.dirname(os.path.abspath(__file__))     
    parent_dir = os.path.abspath(os.path.join(base_dir, ".."))
    file_path = os.path.join(parent_dir, "proxies", "proxies.json")

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            proxies = data["proxies"]
        
        logger.info("Loaded proxies from %s", file_path)
    
    except FileNotFoundError:
        logger.warning("Proxies file not found at %s", file_path)


    url = "https://www.imoti.net/bg/sredni-ceni"

    try:
        response = requests.get(url, timeout=60, proxies=proxies)
        soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
        price_per_sqm_rows: ResultSet[Any] | Any = soup.find("tbody").find_all("tr")

        total_price = 0
        count = 0
        for row in price_per_sqm_rows:
            cells = row.find_all("td")
            if len(cells) > 1:
                price_cell: Any = cells[1].get_text(strip=True).replace(" ", "")
                try:
                    price: float = float(price_cell)
                    total_price += price
                    count += 1
                except ValueError:
                    continue

        avg_price = total_price / count if count > 0 else None

        logger.info("Computed average EUR price per sqm: %s", avg_price)
        return {"avg_price": avg_price}

    except Exception:
        logger.error("Failed to fetch sqm price")
        return {"error": "Failed to fetch sqm price"}