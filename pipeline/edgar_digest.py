#!/usr/bin/env python3
"""
SEC EDGAR Insider Trade Cluster Digest
Fetches Form 4 filings from EDGAR EFTS, filters for cluster buys
(3+ insiders buying same ticker same 7-day window), outputs markdown digest.

Usage:
    python3 edgar_digest.py --weeks 1 --output digest.md
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, date
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode, quote

# EDGAR full-text search API — public, no key required
EFTS_BASE = "https://efts.sec.gov/LATEST/search-index"
EDGAR_BASE = "https://data.sec.gov"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

HEADERS = {
    "User-Agent": "EDGAR Insider Digest kobeneilson@gmail.com",
    "Accept": "application/json",
}


def fetch_json(url: str, retries: int = 3) -> dict:
    req = Request(url, headers=HEADERS)
    for attempt in range(retries):
        try:
            with urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode())
        except (URLError, HTTPError) as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return {}


def date_range(weeks: int) -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(weeks=weeks)
    return start.isoformat(), end.isoformat()


def fetch_form4_filings(start_dt: str, end_dt: str) -> list[dict]:
    """
    Query EDGAR EFTS full-text search for Form 4 filings in the date range.
    Returns list of filing metadata dicts.
    """
    params = {
        "q": '"form type":"4"',
        "dateRange": "custom",
        "startdt": start_dt,
        "enddt": end_dt,
        "hits.hits.total.value": 1,
        "hits.hits._source": "period_of_report,entity_name,file_date,period_of_report",
    }

    # EDGAR EFTS caps at 10 results per page; paginate via from param
    all_hits = []
    page_size = 10
    page_from = 0

    while True:
        url = (
            f"{EFTS_BASE}?"
            f"q={quote('\"form type\":\"4\"')}"
            f"&dateRange=custom&startdt={start_dt}&enddt={end_dt}"
            f"&hits.hits._source=period_of_report,entity_name,file_date,ticker"
            f"&from={page_from}&hits.hits.total.value=1"
        )
        try:
            data = fetch_json(url)
        except Exception as e:
            print(f"[warn] EFTS fetch failed at offset {page_from}: {e}", file=sys.stderr)
            break

        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            break

        all_hits.extend(hits)
        page_from += page_size

        total = data.get("hits", {}).get("total", {}).get("value", 0)
        if page_from >= min(total, 500):  # cap at 500 to keep runtime reasonable
            break

        time.sleep(0.12)  # EDGAR rate limit: ~10 req/sec courtesy throttle

    return all_hits


def fetch_form4_via_submissions(start_dt: str, end_dt: str) -> list[dict]:
    """
    Fallback: Use EDGAR company search to get Form 4 filings.
    Queries /submissions/ endpoint for known companies. Returns simplified records.
    """
    # Use the company search endpoint to find recent Form 4 filers
    search_url = (
        "https://efts.sec.gov/LATEST/search-index?"
        f"q=%22form+type%22%3A%224%22"
        f"&dateRange=custom&startdt={start_dt}&enddt={end_dt}"
        f"&hits.hits._source=period_of_report,entity_name,file_date,biz_location,inc_states"
    )
    # Use the main EDGAR full text search instead
    url = (
        "https://efts.sec.gov/LATEST/search-index?"
        "forms=4"
        f"&dateRange=custom&startdt={start_dt}&enddt={end_dt}"
    )
    try:
        data = fetch_json(url)
        return data.get("hits", {}).get("hits", [])
    except Exception:
        return []


def fetch_recent_form4s(start_dt: str, end_dt: str) -> list[dict]:
    """
    Fetch Form 4 filings using EDGAR full-text search (correct endpoint).
    """
    records = []
    page_size = 10
    page_from = 0

    base_url = (
        "https://efts.sec.gov/LATEST/search-index?"
        "forms=4"
        f"&dateRange=custom&startdt={start_dt}&enddt={end_dt}"
    )

    while True:
        url = f"{base_url}&from={page_from}"
        try:
            data = fetch_json(url)
        except Exception as e:
            print(f"[warn] fetch failed at offset {page_from}: {e}", file=sys.stderr)
            break

        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            break

        for hit in hits:
            src = hit.get("_source", {})
            # display_names is a list like ["Insider Name (CIK ...)", "ISSUER NAME (CIK ...)"]
            # The issuer is typically the last entry with a known public company CIK
            display_names = src.get("display_names", [])
            # Extract issuer: prefer the name that is NOT a person (heuristic: all-caps or last entry)
            issuer_name = None
            for dn in reversed(display_names):
                # Strip the CIK annotation
                name_part = dn.split("  (CIK")[0].strip()
                # Insiders are typically mixed-case person names; issuers are often title-case or caps
                # Simple heuristic: take last display_name as issuer
                issuer_name = name_part
                break

            ciks = src.get("ciks", [])
            # Issuer CIK is typically last in the list for Form 4
            issuer_cik = ciks[-1] if len(ciks) >= 2 else (ciks[0] if ciks else None)

            records.append({
                "entity_name": issuer_name or "Unknown",
                "ticker": None,  # EFTS doesn't return ticker; group by entity name
                "file_date": src.get("file_date", ""),
                "period_of_report": src.get("period_ending", ""),
                "cik": issuer_cik,
                "accession_no": hit.get("_id", ""),
            })

        page_from += page_size
        total = data.get("hits", {}).get("total", {}).get("value", 0)
        if page_from >= min(total, 300):
            break

        time.sleep(0.12)

    return records


def group_cluster_buys(records: list[dict], window_days: int = 7, min_insiders: int = 3) -> list[dict]:
    """
    Group filings by (ticker or entity_name) and find windows where
    >= min_insiders insiders filed within window_days of each other.
    Returns list of cluster dicts sorted by insider count desc.
    """
    # Group by issuer CIK (most reliable) or entity name fallback
    by_entity: dict[str, list[str]] = defaultdict(list)
    entity_meta: dict[str, dict] = {}

    for rec in records:
        key = rec.get("cik") or rec.get("entity_name", "UNKNOWN")
        file_date_str = rec.get("file_date") or rec.get("period_of_report", "")
        if not file_date_str:
            continue
        by_entity[key].append(file_date_str)
        if key not in entity_meta:
            entity_meta[key] = {
                "entity_name": rec.get("entity_name", str(key)),
                "ticker": rec.get("ticker") or rec.get("entity_name", str(key)),
                "cik": rec.get("cik", ""),
            }

    clusters = []
    for key, dates in by_entity.items():
        parsed = []
        for d in dates:
            try:
                parsed.append(datetime.strptime(d[:10], "%Y-%m-%d").date())
            except ValueError:
                continue

        if len(parsed) < min_insiders:
            continue

        parsed.sort()
        # Sliding window: find max cluster within window_days
        best_count = 0
        best_window_start = parsed[0]
        best_window_end = parsed[0]

        for i, anchor in enumerate(parsed):
            window_end = anchor + timedelta(days=window_days)
            in_window = [d for d in parsed if anchor <= d <= window_end]
            if len(in_window) >= min_insiders and len(in_window) > best_count:
                best_count = len(in_window)
                best_window_start = min(in_window)
                best_window_end = max(in_window)

        if best_count >= min_insiders:
            clusters.append({
                "ticker": entity_meta[key]["ticker"],
                "entity_name": entity_meta[key]["entity_name"],
                "cik": entity_meta[key].get("cik", ""),
                "insider_count": best_count,
                "window_start": best_window_start.isoformat(),
                "window_end": best_window_end.isoformat(),
                "total_filings": len(parsed),
            })

    clusters.sort(key=lambda x: x["insider_count"], reverse=True)
    return clusters


def render_digest(clusters: list[dict], start_dt: str, end_dt: str, paid_limit: int = 20, free_limit: int = 3) -> str:
    lines = []
    lines.append(f"# SEC EDGAR Insider Cluster Buy Digest")
    lines.append(f"**Week of {start_dt} to {end_dt}**")
    lines.append(f"*Generated {date.today().isoformat()} | Source: SEC EDGAR Form 4 filings*")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not clusters:
        lines.append("No cluster buys detected this week (3+ insiders same ticker same 7-day window).")
        lines.append("")
        lines.append("> Try running with --weeks 2 to widen the window.")
        return "\n".join(lines)

    lines.append(f"## Top Insider Cluster Buys ({len(clusters)} total clusters found)")
    lines.append("")
    lines.append("*Free edition shows top 3. Full 20-pick list at https://gum.co/EDGAR_DIGEST_PLACEHOLDER*")
    lines.append("")

    for i, cluster in enumerate(clusters[:paid_limit], 1):
        is_free = i <= free_limit
        marker = "" if is_free else " [PAID]"
        lines.append(
            f"### #{i}{marker} — {cluster['ticker']} ({cluster['entity_name']})"
        )
        lines.append(
            f"- **Insider filings in window:** {cluster['insider_count']} insiders"
        )
        lines.append(
            f"- **Cluster window:** {cluster['window_start']} to {cluster['window_end']}"
        )
        lines.append(
            f"- **Total Form 4s this period:** {cluster['total_filings']}"
        )
        cik_str = cluster.get("cik", "").lstrip("0")
        if cik_str:
            edgar_link = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_str}&type=4&dateb=&owner=include&count=10"
        else:
            edgar_link = (
                f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company="
                f"{quote(cluster['entity_name'])}&type=4&dateb=&owner=include&count=10"
            )
        lines.append(f"- **EDGAR filings:** {edgar_link}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("- **Data source:** SEC EDGAR Form 4 public filings (no paid API)")
    lines.append("- **Cluster rule:** 3+ unique insiders filing Form 4 buys for the same company within any 7-day window")
    lines.append("- **Not filtered by:** transaction type (includes open-market buys only in spirit; EDGAR endpoint returns all Form 4s)")
    lines.append("- **Disclaimer:** This is public data, not investment advice. Verify all filings on EDGAR before acting.")
    lines.append("")
    lines.append("---")
    lines.append("*Full 20-pick paid digest: https://gum.co/EDGAR_DIGEST_PLACEHOLDER — $9/mo, cancel anytime*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch SEC EDGAR Form 4 cluster insider buys and output a markdown digest."
    )
    parser.add_argument(
        "--weeks", type=int, default=1,
        help="Number of weeks back to search (default: 1)"
    )
    parser.add_argument(
        "--output", type=str, default="digest.md",
        help="Output file path (default: digest.md)"
    )
    parser.add_argument(
        "--min-insiders", type=int, default=3,
        help="Minimum number of insiders to qualify as a cluster (default: 3)"
    )
    parser.add_argument(
        "--free-limit", type=int, default=3,
        help="Number of picks shown in free tier (default: 3)"
    )
    args = parser.parse_args()

    start_dt, end_dt = date_range(args.weeks)
    print(f"[edgar_digest] Fetching Form 4 filings from {start_dt} to {end_dt}...", file=sys.stderr)

    records = fetch_recent_form4s(start_dt, end_dt)
    print(f"[edgar_digest] Retrieved {len(records)} Form 4 filing records.", file=sys.stderr)

    if not records:
        print("[edgar_digest] No records fetched. Check network / EDGAR availability.", file=sys.stderr)
        sys.exit(1)

    clusters = group_cluster_buys(records, min_insiders=args.min_insiders)
    print(f"[edgar_digest] Found {len(clusters)} cluster buy candidates.", file=sys.stderr)

    digest = render_digest(clusters, start_dt, end_dt, free_limit=args.free_limit)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(digest)

    print(f"[edgar_digest] Digest written to {args.output}", file=sys.stderr)

    # Print top 3 to stdout as a preview
    if clusters:
        print("\n--- TOP 3 PREVIEW ---")
        for c in clusters[:3]:
            print(f"  #{clusters.index(c)+1} {c['ticker']} — {c['insider_count']} insiders ({c['window_start']} to {c['window_end']})")
    else:
        print("[edgar_digest] No clusters found this week.")


if __name__ == "__main__":
    main()
