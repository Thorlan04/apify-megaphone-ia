#!/usr/bin/env python3
"""
github_seo_optimizer.py - Autonomous GitHub Repository Topics & SEO Optimizer
Part of ai_megaphone for Thorlan04

Automatically configures high-intent search topics (tags) on Thorlan04's
public GitHub repositories using the GitHub API and GITHUB_TOKEN.
This maximizes discovery when developers search for MCP tools, Apify actors,
Shopify scrapers, and B2B compliance checkers directly on GitHub.
Cost: 0 €
"""

import json
import logging
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [GITHUB-SEO] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ai_megaphone.github_seo")

BASE_DIR = Path(__file__).resolve().parent
DISCOVERED_CACHE = BASE_DIR / "discovered_ecosystem.json"
GITHUB_USER = os.getenv("GITHUB_USERNAME", "Thorlan04")

# Curated high-intent SEO topics targeted for AI agents, MCP and B2B developers
REPO_TOPIC_RULES: Dict[str, List[str]] = {
    "eu-b2b-compliance-ai-auditor": [
        "apify-actor", "mcp-server", "b2b-compliance", "siret-validator",
        "siren-api", "vies-vat", "gdpr-compliance", "eaa-2025",
        "llms-txt", "ai-readiness", "kyc-automation", "claude-desktop"
    ],
    "shopify-fast-catalog-products-json": [
        "shopify-scraper", "apify-actor", "mcp-server", "ecommerce-scraping",
        "products-json", "price-monitor", "inventory-tracker", "dropshipping",
        "n8n-nodes", "make-com"
    ],
    "apify-b2b-autopilot-pack": [
        "apify-actor", "mcp-server", "ai-agents", "llms-txt",
        "b2b-automation", "rag-markdown", "n8n", "make-com",
        "web-scraping", "lead-generation"
    ],
    "global-compatibility-matrix-agent": [
        "compatibility-matrix", "parts-finder", "cross-reference",
        "hardware-compatibility", "github-pages", "open-data", "catalog-engine"
    ],
    "auto-consumables-agent": [
        "consumables-finder", "compatibility-engine", "auto-parts",
        "cross-reference", "github-pages", "smart-matrix"
    ],
    "auto-outdoor-parts-agent": [
        "outdoor-parts", "compatibility-matrix", "spare-parts-catalog",
        "lawnmower-parts", "github-pages", "equipment-matrix"
    ],
    "apify-megaphone-ia": [
        "mcp-server", "generative-engine-optimization", "indexnow",
        "llms-txt", "apify-actor", "b2b-lead-generation", "ai-agents",
        "claude-desktop", "cursor-ai", "perplexity-seo"
    ],
    "apify-autonomous-factory-brain": [
        "apify-actor", "autonomous-agents", "actor-factory", "ai-pipeline",
        "automation", "b2b-ai"
    ],
    "prompt-generator": [
        "prompt-engineering", "prompt-generator", "ai-prompts",
        "llm-tools", "cursor-ai", "chatgpt"
    ]
}

DEFAULT_TOPICS = [
    "ai-agents", "mcp-server", "apify-actor", "b2b-automation",
    "open-source", "llms-txt"
]


def clean_topic(topic: str) -> str:
    """GitHub topics must be lowercase, alphanumeric, with hyphens, max 35 chars."""
    cleaned = re.sub(r"[^a-z0-9-]", "", topic.lower().strip().replace("_", "-"))
    return cleaned[:35]


def update_repository_topics(repo_name: str, topics: List[str], token: str) -> bool:
    """Updates topics on a single repository via GitHub REST API."""
    cleaned_topics = list(dict.fromkeys([clean_topic(t) for t in topics if clean_topic(t)]))[:20]
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/topics"

    payload = json.dumps({"names": cleaned_topics}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.mercy-preview+json",
            "User-Agent": "Thorlan04Megaphone/1.0"
        },
        method="PUT"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 204):
                logger.info(f"Updated topics for {repo_name}: {cleaned_topics}")
                return True
            else:
                logger.warning(f"Unexpected status code {resp.status} updating topics for {repo_name}")
                return False
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        logger.warning(f"Failed to update topics on {repo_name} (HTTP {e.code}): {err_msg[:100]}")
        return False
    except Exception as e:
        logger.warning(f"Exception updating topics on {repo_name}: {e}")
        return False


def optimize_github_seo() -> Dict[str, Any]:
    """Applies curated SEO topics across all discovered repositories if GITHUB_TOKEN is available."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.info("No GITHUB_TOKEN provided with write access. Skipping repository topic update (this is normal in local test mode).")
        return {
            "status": "skipped",
            "reason": "Missing GITHUB_TOKEN",
            "suggested_topics": REPO_TOPIC_RULES
        }

    # Load repos from cache or discover
    repos = []
    if DISCOVERED_CACHE.exists():
        try:
            with open(DISCOVERED_CACHE, "r", encoding="utf-8") as f:
                data = json.load(f)
                repos = data.get("github_repositories", [])
        except Exception:
            pass

    if not repos:
        from ai_megaphone.discover_github_repos import build_ecosystem
        data = build_ecosystem(verify_online=False)
        repos = data.get("github_repositories", [])

    results = {}
    for r in repos:
        name = r.get("name")
        if not name:
            continue
        topics_to_set = REPO_TOPIC_RULES.get(name, DEFAULT_TOPICS)
        # Merge existing topics without duplicates
        existing = r.get("topics", [])
        combined = list(dict.fromkeys(topics_to_set + existing))
        success = update_repository_topics(name, combined, token=token)
        results[name] = {"success": success, "topics": combined}

    return {"status": "completed", "results": results}


if __name__ == "__main__":
    out = optimize_github_seo()
    print(f"\n[OK] GitHub SEO Optimizer finished: {out['status']}")
    if out.get("reason"):
        print(f"  Note: {out['reason']}")
    elif out.get("results"):
        print(f"  Updated {len(out['results'])} repositories.")
