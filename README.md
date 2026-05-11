# SEC EDGAR Insider Trade Alert Digest

Weekly digest of cluster insider purchases from SEC EDGAR for retail investors.

**Live at:** https://gum.co/EDGAR_DIGEST_PLACEHOLDER  
**Kill date:** 2026-06-10  
**Kill signal:** <5 paid subscribers by day 30

## What It Does

Fetches public Form 4 filings from SEC EDGAR, filters for "cluster buys" (3+ insiders buying the same ticker in the same 7-day window), and outputs a ranked markdown digest. Free tier = top 3 picks. Paid ($9/mo Gumroad) = full 20-pick list.

## Structure

```
sec-edgar-insider-digest/
  site/           Landing page (static HTML)
  pipeline/       edgar_digest.py — fetch, filter, output
  DISTRIBUTE.md   Reddit drop kit + Gumroad copy
```

## Running the Pipeline

```bash
pip install requests
python3 pipeline/edgar_digest.py --weeks 1 --output digest.md
```

Requires Python 3.8+. No paid APIs. No API keys. Uses only SEC EDGAR's public EFTS endpoint.

## Distribution

Weekly post to r/ValueInvesting with top 3 picks free. Full 20-pick list via Gumroad subscription.

## License

MIT
