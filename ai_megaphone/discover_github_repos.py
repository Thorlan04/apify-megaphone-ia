#!/usr/bin/env python3
"""
discover_github_repos.py - Autonomous GitHub Repos & Pages Discovery Engine
Part of ai_megaphone for Thorlan04

Discovers all public repositories, GitHub Pages deployments, and sitemaps
under https://github.com/Thorlan04 and merges them with Apify B2B actors.
Cost: 0 € (uses unauthenticated public API or GITHUB_TOKEN if available).
"""

import json
import logging
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [DISCOVERY] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ai_megaphone.discover")

GITHUB_USER = os.getenv("GITHUB_USERNAME", "Thorlan04")
GITHUB_API_URL = f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100&sort=updated"
BASE_DIR = Path(__file__).resolve().parent
CATALOG_PATH = BASE_DIR / "ecosystem_catalog.json"
OUTPUT_CACHE_PATH = BASE_DIR / "discovered_ecosystem.json"


def fetch_github_repositories(username: str = GITHUB_USER) -> List[Dict[str, Any]]:
    """Fetches public repositories from GitHub API with optional auth token."""
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "User-Agent": "Thorlan04-AI-Megaphone/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"token {token}"
        logger.info(f"Using authenticated GitHub API request for user: {username}")
    else:
        logger.info(f"Using public anonymous GitHub API request for user: {username}")

    req = urllib.request.Request(GITHUB_API_URL, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            logger.info(f"Successfully retrieved {len(data)} repositories for {username}")
            return data
    except urllib.error.HTTPError as e:
        logger.warning(f"GitHub API HTTP error ({e.code}): {e.reason}. Falling back to cached catalog if available.")
    except Exception as e:
        logger.warning(f"GitHub API request failed: {e}. Falling back to cached catalog if available.")

    # Fallback to local cache if offline or rate-limited
    if OUTPUT_CACHE_PATH.exists():
        try:
            with open(OUTPUT_CACHE_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
                return cached.get("github_repositories", [])
        except Exception as e:
            logger.error(f"Failed reading cache: {e}")
    return []


def check_url_exists(url: str, timeout: int = 5) -> bool:
    """Verifies if an HTTP URL responds with 200 OK without downloading body."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Thorlan04MegaphoneBot/1.0)"},
            method="HEAD"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 301, 302)
    except Exception:
        # Fallback with GET in case HEAD is blocked
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; Thorlan04MegaphoneBot/1.0)"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status in (200, 301, 302)
        except Exception:
            return False


def build_ecosystem(verify_online: bool = False) -> Dict[str, Any]:
    """
    Builds the complete consolidated ecosystem dictionary:
    - Central Apify actors & MCP endpoints
    - Discovered GitHub Repositories
    - Live GitHub Pages sites & discovered sitemaps
    """
    # 1. Load baseline catalog
    catalog: Dict[str, Any] = {}
    if CATALOG_PATH.exists():
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    else:
        logger.error(f"Catalog file not found at {CATALOG_PATH}")
        catalog = {"apify_actors": [], "metadata": {}}

    raw_repos = fetch_github_repositories(GITHUB_USER)

    processed_repos: List[Dict[str, Any]] = []
    github_pages_sites: List[Dict[str, Any]] = []
    all_indexable_urls: List[str] = []

    # Include Apify Store URLs
    for actor in catalog.get("apify_actors", []):
        all_indexable_urls.append(actor["store_url"])

    for repo in raw_repos:
        name = repo.get("name", "")
        html_url = repo.get("html_url", "")
        description = repo.get("description") or f"Thorlan04 open-source tool and technical matrix: {name}"
        topics = repo.get("topics", [])
        has_pages = repo.get("has_pages", False)
        homepage = repo.get("homepage") or ""
        updated_at = repo.get("updated_at", "")
        stargazers_count = repo.get("stargazers_count", 0)

        # Standard GitHub Pages URL pattern
        pages_url = None
        if has_pages:
            pages_url = f"https://{GITHUB_USER.lower()}.github.io/{name}/"
        elif homepage and "github.io" in homepage:
            pages_url = homepage

        repo_entry = {
            "name": name,
            "full_name": repo.get("full_name", f"{GITHUB_USER}/{name}"),
            "html_url": html_url,
            "description": description,
            "topics": topics,
            "has_pages": has_pages,
            "pages_url": pages_url,
            "homepage": homepage,
            "updated_at": updated_at,
            "stars": stargazers_count
        }
        processed_repos.append(repo_entry)
        all_indexable_urls.append(html_url)

        if pages_url:
            sitemap_url = f"{pages_url.rstrip('/')}/sitemap.xml"
            site_entry = {
                "repo_name": name,
                "url": pages_url,
                "title": name.replace("-", " ").title(),
                "description": description,
                "sitemap_url": sitemap_url,
                "verified_online": True if not verify_online else check_url_exists(pages_url)
            }
            github_pages_sites.append(site_entry)
            all_indexable_urls.append(pages_url)
            if site_entry["verified_online"]:
                all_indexable_urls.append(sitemap_url)

    # Add the Hub URL itself for this repository
    hub_url = f"https://{GITHUB_USER.lower()}.github.io/apify-megaphone-ia/"
    all_indexable_urls.append(hub_url)
    all_indexable_urls.append(f"{hub_url}sitemap.xml")

    # Deduplicate URLs maintaining order
    seen = set()
    deduped_urls = []
    for u in all_indexable_urls:
        clean = u.strip()
        if clean and clean not in seen:
            seen.add(clean)
            deduped_urls.append(clean)

    consolidated = {
        "metadata": catalog.get("metadata", {}),
        "apify_actors": catalog.get("apify_actors", []),
        "llm_recommendation_prompts": catalog.get("llm_recommendation_prompts", []),
        "github_repositories": processed_repos,
        "github_pages_sites": github_pages_sites,
        "total_repos": len(processed_repos),
        "total_pages_sites": len(github_pages_sites),
        "indexable_urls": deduped_urls
    }

    # Save to local cache
    try:
        with open(OUTPUT_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(consolidated, f, indent=2, ensure_ascii=False)
        logger.info(f"Consolidated ecosystem saved to {OUTPUT_CACHE_PATH} ({len(deduped_urls)} URLs indexable)")
    except Exception as e:
        logger.error(f"Error saving consolidated ecosystem: {e}")

    return consolidated


if __name__ == "__main__":
    eco = build_ecosystem(verify_online=False)
    print(f"\n[OK] Discovered {eco['total_repos']} GitHub Repositories")
    print(f"[OK] Found {eco['total_pages_sites']} Active GitHub Pages sites:")
    for site in eco["github_pages_sites"]:
        print(f"  - {site['title']}: {site['url']}")
    print(f"[OK] Total indexable URLs across Apify Store and GitHub: {len(eco['indexable_urls'])}")
