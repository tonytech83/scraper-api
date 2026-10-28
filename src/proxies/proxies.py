import json
import os
import re
from datetime import date

import requests

from src.app_logging import get_logger

logger = get_logger(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "proxies.json")

PROXY_SOURCES = [
    "https://cdn.jsdelivr.net/gh/proxyscrape/free-proxy-list@main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt",
]

# ip:port, e.g. 123.45.67.89:8080
IP_PORT_RE = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d{1,5})$")


def _today() -> str:
    return date.today().isoformat()


def _read_file() -> dict | None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        logger.warning("Proxies file is corrupted, will rebuild: %s", file_path)
        return None


def _write_file(data: dict) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info("Saved %d proxies to %s", len(data["proxies"]), file_path)


def load_cached_proxies() -> list[str]:
    """Return today's proxies, or an empty list if a refresh is needed.

    A refresh is needed when the file is missing, corrupted, from an earlier
    day, or the last download failed.
    """
    data = _read_file()
    if not data:
        return []
    if data.get("date") != _today() or data.get("status") != "OK":
        logger.info("Proxies are stale or last fetch failed; refresh needed")
        return []

    proxies = data.get("proxies", [])
    # tolerate the old {index: url} format
    if isinstance(proxies, dict):
        proxies = list(proxies.values())

    logger.info("Using %d cached proxies from %s", len(proxies), file_path)
    return proxies


def _normalize(line: str) -> str | None:
    """Turn 'ip:port' or 'scheme://ip:port' into 'http://ip:port'; None if invalid."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if "://" in line:
        line = line.split("://", 1)[1]
    m = IP_PORT_RE.match(line)
    if not m:
        return None
    ip, port = m.groups()
    if not all(0 <= int(o) <= 255 for o in ip.split(".")) or not 0 < int(port) <= 65535:
        return None
    return f"http://{ip}:{port}"


def _download() -> list[str]:
    """Return normalized proxies from the first source that yields any."""
    for url in PROXY_SOURCES:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Proxy source failed (%s): %s", url, exc)
            continue

        # dict.fromkeys keeps order while removing duplicates
        proxies = list(
            dict.fromkeys(p for p in map(_normalize, response.text.splitlines()) if p)
        )
        if proxies:
            logger.info("Fetched %d proxies from %s", len(proxies), url)
            return proxies
        logger.warning("Proxy source returned no valid entries: %s", url)

    raise RuntimeError("All proxy sources failed")


def fetch_and_cache_proxies() -> list[str]:
    """Ensure proxies.json holds today's proxy list; return the list.

    Downloads at most once per day. On failure, keeps the previous list
    (if any) and marks status as "Fail" so the next call retries.
    """
    cached = load_cached_proxies()
    if cached:
        return cached

    try:
        proxies = _download()
        _write_file({"status": "OK", "date": _today(), "proxies": proxies})
        return proxies
    except Exception:
        logger.exception("Could not refresh proxies")
        previous = (_read_file() or {}).get("proxies", [])
        if isinstance(previous, dict):
            previous = list(previous.values())
        _write_file({"status": "Fail", "date": _today(), "proxies": previous})
        return previous


def as_requests_proxies(proxy: str) -> dict[str, str]:
    """Build the dict `requests` expects for a single proxy URL."""
    return {"http": proxy, "https": proxy}
