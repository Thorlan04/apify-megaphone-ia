#!/usr/bin/env python3
"""
indexnow_broadcaster.py - Autonomous IndexNow (Central + Bing/ChatGPT) & Open Archival Broadcaster
Part of ai_megaphone v2.0 for Thorlan04

1. Generates and manages the deterministic IndexNow API Key verification file (docs/<key>.txt)
2. Broadcasts all Hub & GEO Solution URLs (.html & .md) simultaneously to:
   - https://api.indexnow.org/indexnow
   - https://www.bing.com/indexnow (Direct feed for ChatGPT Search & Microsoft Copilot)
   - https://yandex.com/indexnow
3. Pings Archive.org Wayback Machine Save API with Apify Store, Hub, and Telegraph URLs.
Cost: 0 €
"""

import hashlib
import json
import logging
import os
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [INDEXNOW] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ai_megaphone.indexnow")

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
DOCS_DIR = REPO_ROOT / "docs"
DISCOVERED_CACHE = BASE_DIR / "discovered_ecosystem.json"
SYNDICATION_LOG = BASE_DIR / "syndication_log.json"

INDEXNOW_ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow"
]
ARCHIVE_ORG_SAVE_ENDPOINT = "https://web.archive.org/save/"
HOST_NAME = "thorlan04.github.io"


def get_or_create_indexnow_key() -> str:
    """
    Returns a persistent 32-character hexadecimal IndexNow key.
    Writes key file to docs/<key>.txt and root <key>.txt.
    """
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    for p in DOCS_DIR.glob("*.txt"):
        name = p.stem
        if len(name) == 32 and all(c in "0123456789abcdef" for c in name.lower()):
            logger.info(f"Using existing IndexNow key file: {p.name}")
            return name

    salt = os.getenv("INDEXNOW_SALT", "thorlan04-b2b-mcp-megaphone-2026")
    key = hashlib.md5(f"thorlan04:{salt}".encode("utf-8")).hexdigest()

    key_file = DOCS_DIR / f"{key}.txt"
    key_file.write_text(key, encoding="utf-8")
    (REPO_ROOT / f"{key}.txt").write_text(key, encoding="utf-8")
    logger.info(f"Generated new IndexNow key verification file at {key_file}")
    return key


def broadcast_to_indexnow(urls: List[str], key: str, host: str = HOST_NAME) -> Dict[str, Any]:
    """Submits Hub and GEO Solution URLs to Central IndexNow, Bing (ChatGPT Search), and Yandex."""
    scope_prefix = f"https://{host}/apify-megaphone-ia"
    filtered_urls = [u for u in urls if u.startswith(scope_prefix)]
    if not filtered_urls:
        logger.warning(f"No URLs matching scope {scope_prefix} found to submit to IndexNow.")
        return {"status": "skipped", "count": 0, "message": "No matching URLs"}

    key_location = f"https://{host}/apify-megaphone-ia/{key}.txt"

    payload = {
        "host": host,
        "key": key,
        "keyLocation": key_location,
        "urlList": filtered_urls
    }

    req_data = json.dumps(payload).encode("utf-8")
    endpoint_results = []
    any_success = False

    for endpoint in INDEXNOW_ENDPOINTS:
        req = urllib.request.Request(
            endpoint,
            data=req_data,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "Thorlan04-IndexNow-Broadcaster/2.0"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                ok = resp.status in (200, 202)
                if ok:
                    any_success = True
                msg = f"{endpoint} -> HTTP {resp.status} ({len(filtered_urls)} URLs)"
                logger.info(f"IndexNow broadcast succeeded: {msg}")
                endpoint_results.append(msg)
        except urllib.error.HTTPError as e:
            msg = f"{endpoint} -> HTTP {e.code}"
            logger.info(f"IndexNow notice: {msg}")
            endpoint_results.append(msg)
        except Exception as e:
            msg = f"{endpoint} -> {e}"
            logger.info(f"IndexNow notice: {msg}")
            endpoint_results.append(msg)

    return {
        "submitted_urls": len(filtered_urls),
        "success": any_success,
        "endpoints": endpoint_results,
        "message": " | ".join(endpoint_results[:2])
    }


def ping_archive_org(urls: List[str], max_urls: int = 5) -> List[Dict[str, Any]]:
    """
    Pings Archive.org Wayback Machine Save API with Apify Store pages, Hub URLs,
    and Telegraph benchmark articles to create permanent public authority citations.
    """
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }

    priority_urls = [u for u in urls if "apify.com" in u or "/solutions/" in u][:max_urls]

    for target_url in priority_urls:
        save_url = f"{ARCHIVE_ORG_SAVE_ENDPOINT}{target_url}"
        item_res = {"url": target_url, "status": "pending"}
        try:
            req = urllib.request.Request(save_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=4) as resp:
                item_res["status_code"] = resp.status
                item_res["status"] = "saved" if resp.status in (200, 302, 201) else f"http_{resp.status}"
                logger.info(f"Wayback Machine saved: {target_url} (HTTP {resp.status})")
        except urllib.error.HTTPError as e:
            item_res["status_code"] = e.code
            item_res["status"] = f"http_{e.code}"
            logger.info(f"Wayback Machine note for {target_url}: HTTP {e.code}")
        except Exception:
            item_res["status"] = "timed_out"
            logger.info(f"Wayback Machine ping queued for {target_url} (non-blocking)")

        results.append(item_res)
        time.sleep(0.4)

    return results


def broadcast_all() -> Dict[str, Any]:
    """Runs key creation, multi-engine IndexNow submission, and archival pings."""
    key = get_or_create_indexnow_key()

    if DISCOVERED_CACHE.exists():
        with open(DISCOVERED_CACHE, "r", encoding="utf-8") as f:
            eco = json.load(f)
    else:
        from ai_megaphone.discover_github_repos import build_ecosystem
        eco = build_ecosystem(verify_online=False)

    indexable_urls = eco.get("indexable_urls", [])

    logger.info(f"Starting multi-engine IndexNow & Archival broadcast for {len(indexable_urls)} ecosystem URLs...")
    indexnow_res = broadcast_to_indexnow(indexable_urls, key=key)
    archival_res = ping_archive_org(indexable_urls, max_urls=4)

    return {
        "indexnow_key": key,
        "indexnow_result": indexnow_res,
        "archival_pings": archival_res
    }


if __name__ == "__main__":
    res = broadcast_all()
    print("\n[OK] Broadcast complete:")
    print(f"  - IndexNow key: {res['indexnow_key']}")
    print(f"  - IndexNow Status: {res['indexnow_result']['message']}")
    print(f"  - Archive.org pings: {len(res['archival_pings'])} URLs targeted")
