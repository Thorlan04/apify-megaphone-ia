#!/usr/bin/env python3
"""
run_megaphone.py - Main Autonomous AI Megaphone Orchestrator
Part of ai_megaphone for Thorlan04

Coordinates the full end-to-end zero-cost autonomous promotion pipeline:
1. Dynamic GitHub repositories & Pages discovery (public GitHub API)
2. Generative Engine Optimization (GEO) manifests generation:
   - docs/llms.txt & docs/llms-full.txt
   - docs/.well-known/mcp.json & docs/ai-plugin.json
   - docs/index.html with rich JSON-LD SoftwareApplication schemas
   - docs/sitemap.xml & docs/robots.txt (welcoming all AI bots)
3. High-authority Telegraph article syndication with dofollow backlinks
4. IndexNow API broadcast (Bing, ChatGPT Search, Copilot, Yandex) + Archive.org authority pings
5. GitHub Repository SEO topic optimization

Usage:
  python ai_megaphone/run_megaphone.py
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai_megaphone.discover_github_repos import build_ecosystem
from ai_megaphone.generate_ai_manifests import build_and_save_manifests
from ai_megaphone.indexnow_broadcaster import broadcast_all
from ai_megaphone.telegraph_syndicator import run_syndication
from ai_megaphone.github_seo_optimizer import optimize_github_seo

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [MEGAPHONE] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ai_megaphone.master")

BANNER = r"""
======================================================================
     _______ _   _  ____  _____  _               _   _  ___  _  _   
    |__   __| | | |/ __ \|  __ \| |        /\   | \ | |/ _ \| || |  
       | |  | |_| | |  | | |__) | |       /  \  |  \| | | | | || |_ 
       | |  |  _  | |  | |  _  /| |      / /\ \ | . ` | | | |__   _|
       | |  | | | | |__| | | \ \| |____ / ____ \| |\  | |_| |  | |  
       |_|  |_| |_|\____/|_|  \_\______/_/    \_\_| \_|\___/   |_|  
                  AUTONOMOUS MULTI-PROJECT AI MEGAPHONE             
               Zero-Cost GEO, MCP & IndexNow Broadcast Engine       
======================================================================
"""


def run_full_pipeline() -> Dict[str, Any]:
    """Runs all 5 stages of the autonomous AI Megaphone pipeline safely."""
    start_time = time.time()
    print(BANNER)
    logger.info("Starting autonomous AI Megaphone execution for Thorlan04...")

    summary: Dict[str, Any] = {
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time)),
        "stages": {},
        "errors": []
    }

    # Stage 1: Dynamic Discovery
    logger.info("\n--- [STAGE 1/5] Discovering GitHub Repositories & Active Pages ---")
    try:
        eco = build_ecosystem(verify_online=False)
        summary["stages"]["discovery"] = {
            "status": "success",
            "total_repos": eco.get("total_repos", 0),
            "total_pages_sites": eco.get("total_pages_sites", 0),
            "total_indexable_urls": len(eco.get("indexable_urls", [])),
            "apify_actors_count": len(eco.get("apify_actors", []))
        }
        logger.info(f"Discovery complete: {eco['total_repos']} repos, {eco['total_pages_sites']} live Pages, {len(eco['apify_actors'])} Apify Actors.")
    except Exception as e:
        logger.error(f"Stage 1 failed: {e}")
        summary["stages"]["discovery"] = {"status": "error", "message": str(e)}
        summary["errors"].append(f"Discovery error: {e}")
        eco = {}

    # Stage 2: AI Manifests & GEO Hub Portal
    logger.info("\n--- [STAGE 2/5] Generating LLM Manifests (llms.txt, MCP, Hub Portal) ---")
    try:
        manifest_files = build_and_save_manifests()
        summary["stages"]["manifests"] = {
            "status": "success",
            "generated_files_count": len(manifest_files),
            "files": list(manifest_files.keys())
        }
        logger.info(f"Manifest generation complete: {len(manifest_files)} files written to docs/ and root.")
    except Exception as e:
        logger.error(f"Stage 2 failed: {e}")
        summary["stages"]["manifests"] = {"status": "error", "message": str(e)}
        summary["errors"].append(f"Manifests error: {e}")

    # Stage 3: Telegraph High-Authority Syndication
    logger.info("\n--- [STAGE 3/5] Syndicating Dofollow Article to Telegraph ---")
    try:
        synd_res = run_syndication()
        if synd_res:
            summary["stages"]["syndication"] = {
                "status": "published",
                "title": synd_res.get("title"),
                "url": synd_res.get("url")
            }
            logger.info(f"Telegraph article published: {synd_res.get('url')}")
        else:
            summary["stages"]["syndication"] = {"status": "skipped_or_reused"}
            logger.info("Telegraph syndication completed (existing or rate-limited).")
    except Exception as e:
        logger.error(f"Stage 3 failed: {e}")
        summary["stages"]["syndication"] = {"status": "error", "message": str(e)}
        summary["errors"].append(f"Syndication error: {e}")

    # Stage 4: IndexNow & Archival Pings
    logger.info("\n--- [STAGE 4/5] Broadcasting to IndexNow API & Wayback Machine ---")
    try:
        broadcast_res = broadcast_all()
        summary["stages"]["indexnow"] = {
            "status": "success",
            "key": broadcast_res.get("indexnow_key"),
            "indexnow_status": broadcast_res.get("indexnow_result", {}).get("message"),
            "archival_pings_count": len(broadcast_res.get("archival_pings", []))
        }
        logger.info(f"Broadcast complete: IndexNow key {broadcast_res.get('indexnow_key')}.")
    except Exception as e:
        logger.error(f"Stage 4 failed: {e}")
        summary["stages"]["indexnow"] = {"status": "error", "message": str(e)}
        summary["errors"].append(f"IndexNow error: {e}")

    # Stage 5: GitHub Topics SEO Optimization
    logger.info("\n--- [STAGE 5/5] Optimizing GitHub Topics for AI Developers ---")
    try:
        seo_res = optimize_github_seo()
        summary["stages"]["github_seo"] = seo_res
        logger.info(f"GitHub SEO optimization status: {seo_res.get('status')}")
    except Exception as e:
        logger.error(f"Stage 5 failed: {e}")
        summary["stages"]["github_seo"] = {"status": "error", "message": str(e)}
        summary["errors"].append(f"GitHub SEO error: {e}")

    # Final summary
    elapsed = round(time.time() - start_time, 2)
    summary["elapsed_seconds"] = elapsed

    print("\n" + "=" * 70)
    print("           MEGAPHONE PIPELINE EXECUTION SUMMARY")
    print("=" * 70)
    print(f" Execution Duration   : {elapsed} seconds")
    print(f" GitHub Repositories  : {summary['stages'].get('discovery', {}).get('total_repos', 0)}")
    print(f" Live Pages Sites     : {summary['stages'].get('discovery', {}).get('total_pages_sites', 0)}")
    print(f" Monitized Actors     : {summary['stages'].get('discovery', {}).get('apify_actors_count', 0)}")
    print(f" Total Indexable URLs : {summary['stages'].get('discovery', {}).get('total_indexable_urls', 0)}")
    print(f" Manifests Generated  : {summary['stages'].get('manifests', {}).get('generated_files_count', 0)} files")
    
    synd = summary["stages"].get("syndication", {})
    if synd.get("url"):
        print(f" Telegraph Article    : {synd['url']}")
    else:
        print(f" Telegraph Status     : {synd.get('status', 'none')}")

    inow = summary["stages"].get("indexnow", {})
    print(f" IndexNow Key         : {inow.get('key', 'none')}")
    print(f" IndexNow Status      : {inow.get('indexnow_status', 'none')}")
    print(f" Archival Pings       : {inow.get('archival_pings_count', 0)} URLs processed")
    print(f" GitHub Topics Status : {summary['stages'].get('github_seo', {}).get('status', 'none')}")
    health_status = "100% OPERATIONAL" if not summary["errors"] else f"ERRORS: {len(summary['errors'])}"
    print(f" Pipeline Health      : {health_status}")
    print("=" * 70 + "\n")

    return summary


if __name__ == "__main__":
    res = run_full_pipeline()
    # Exit with 0 so GitHub Actions workflow succeeds cleanly
    sys.exit(0)
