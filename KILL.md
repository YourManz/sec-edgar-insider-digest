# Kill File — sec-edgar-insider-digest

**Kill date:** 2026-06-10
**Kill signal:** Fewer than 5 paid subscribers by 2026-06-10
**Today:** 2026-05-12

---

## Kill Action

If kill signal is met on 2026-06-10:

```bash
cd ~/Work/ventures/sec-edgar-insider-digest
git tag killed/sec-edgar-insider-digest
mkdir -p ~/Work/ventures/_killed
mv ~/Work/ventures/sec-edgar-insider-digest ~/Work/ventures/_killed/
```

Then update the vault note at `~/Documents/Brainstorm/Factory/sec-edgar-insider-digest.md`:
- Change `status: live` → `status: killed`
- Add `killed-date: 2026-06-10`

---

## Promote Action

If kill signal NOT met by day 30 and trajectory is upward:
1. Update vault note: `status: optimizing`
2. Add weekly email digest format, post to r/SecurityAnalysis

---

## Week-by-Week Check-in

| Day | Check | Action if red |
|-----|-------|---------------|
| 7   | Any sales/clients? | If 0: try alternate distribution angle |
| 14  | 1+ sale/client?    | If 0: rewrite headline, repost |
| 21  | 2+ sales/clients?  | If 1: get testimonial, use as social proof |
| 30  | Kill signal check  | If met: run kill action above |
