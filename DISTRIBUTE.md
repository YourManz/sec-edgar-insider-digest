# DISTRIBUTE.md — SEC EDGAR Insider Digest Drop Kit

## Launch Post — r/ValueInvesting

**Flair:** Tools & Resources (or DD)

**Title (≤300 chars):**
I track insider cluster buys from EDGAR every week — here's this week's top 10 [free]

**Body:**

Every week I run a script against SEC EDGAR's public Form 4 database and pull out what I call "cluster buys" — stocks where 3 or more insiders (directors, officers, major holders) all bought shares within the same 7-day window.

One insider buying is noise. Three insiders buying the same stock in the same week is worth paying attention to.

Here's this week's top 10 (full 20-pick list in the digest linked below):

---

**#1 — Meridian Capital Corp (MCC)**
CFO, CEO, and one independent director all filed Form 4 buys between Monday and Wednesday. Open-market purchases, not option exercises. Combined: ~$420K in shares.

**#2 — Ironclad Specialty Materials (ICLAD)**
Four insiders, including the Chairman and two division heads, bought within a 4-day window. First cluster buy on this ticker in 14 months.

**#3 — Greyrock Financial Group (GRYF)**
COO and two board members filed on the same day. Small float — $3M in insider buys on a $40M market cap stock. Cluster density is the highest I've seen this quarter.

*(and 7 more in the digest)*

---

**How I build this:**

No paywalled terminals. No Bloomberg. Just the public EDGAR EFTS search API + a Python script I run every Sunday. It takes about 15 minutes end-to-end. The script groups Form 4 filings by issuer CIK, then finds windows where 3+ filings land within 7 days.

Not investment advice — just a way to surface situations where multiple smart-money insiders are putting their own capital to work at the same time.

Full 20-pick digest (with $ amounts, roles, and EDGAR filing links): https://gum.co/EDGAR_DIGEST_PLACEHOLDER

$9/mo subscription — first week free.

---

## Response Templates

### "Why not just use OpenInsider?"

> OpenInsider is great for browsing individual stocks, but it doesn't surface cluster signals across the whole market automatically. You'd need to already know which ticker to look at. This digest runs the full Form 4 feed and bubbles up the clusters you wouldn't think to check. Different tool for a different use case.

### "This is just Form 4 data anyone can get"

> Totally true — all of this is public EDGAR data, and the script is open source (MIT license on GitHub). The value isn't the data itself, it's the weekly curation and the cluster filter. You could build this yourself in an afternoon. If you do, great. If you'd rather pay $9 to get the output every Monday morning without the setup, that's what this is.

### "How do I know these picks are real/unbiased?"

> Every pick links directly to the SEC EDGAR filing page. You can verify every transaction in under 30 seconds. I don't take any positions in the stocks I feature, and I have no financial relationship with any company on the list. It's just a mechanical filter on public government data — there's no editorial discretion in the ranking.

---

## Week-1 Action Checklist

**Day 1 (Sunday):**
1. `cd pipeline && python3 edgar_digest.py --weeks 1 --output digest.md`
2. Open digest.md — manually verify top 3 picks by clicking their EDGAR links
3. Write the Reddit post body (use 3 of the real picks from digest output)
4. Post to r/ValueInvesting between 9am–11am Eastern (peak traffic window)
5. Reply to first 3 comments within 30 minutes of posting

**Day 3:**
- If post has >10 upvotes: post a follow-up comment: "Update: added insider role breakdown to the full digest. DM if you want the paid link."
- If post has <10 upvotes: try r/stocks or r/investing with a different title angle

**Day 7:**
- Check Gumroad dashboard: if <3 DMs asking for paid version and 0 paid subscribers → rewrite the Reddit post angle (try leading with a specific past cluster that played out well)
- Run pipeline again for the new week; post second weekly edition

**Day 30 — Kill/Promote Decision:**
- Kill signal: <5 paid subscribers AND <3 Gumroad page visits/day average → shut down, archive repo
- Promote signal: >15 paid subscribers → consider a Substack migration for better email deliverability + higher price point ($19/mo)

---

## Gumroad Listing Copy

**Title:** SEC EDGAR Insider Cluster Buy Digest — Weekly Report

**Description:**
Every Monday I publish a digest of the week's highest-conviction insider cluster buys sourced directly from SEC EDGAR Form 4 filings — no paywalled data, no paid APIs, just the public record filtered for signal.

The cluster rule is simple: 3 or more company insiders (officers, directors, major holders) must have each filed a Form 4 buy within the same 7-day window. One insider buying is noise. A cluster is worth a closer look.

Each pick includes the number of insiders, the cluster window dates, the roles of the buyers, and a direct link to the EDGAR filing page so you can verify everything in 30 seconds. Free preview shows the top 3 picks. Paid subscription ($9/mo) unlocks the full 20-pick ranked list.

Cancel anytime. No lock-in.

**Tags:** insider trading, SEC EDGAR, Form 4, stock research, value investing
