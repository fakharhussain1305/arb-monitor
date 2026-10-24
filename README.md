# Cross-Venue Prediction Market Spread Monitor

The same question, such as "Who will be the Democratic nominee in 2028?", is often listed on several prediction-market exchanges at once. If one venue sells YES for 40¢ while another will buy it for 45¢, buying on the first and selling on the second locks in 5¢ whatever happens. That is arbitrage.

This project measures how often that really happens. Since 23 June 2026 it has recorded every apparent cross-venue spread across five venues, roughly every two hours, building a dataset of 43,000 observations. The short answer: **between reputable venues, real spreads are small and rare, and most large spreads turn out to be data problems on smaller venues.**

Part of a wider prediction-market project alongside [polymarket-quant-bot](https://github.com/fakharhussain1305/polymarket-quant-bot).

---

## How it works

`arb_logger.py` calls the [PMXT](https://pypi.org/project/pmxt/) router, which matches equivalent markets across venues and returns the best buy and sell price for each pair. Every pair with a positive spread is appended to `arb_opportunities.csv`, together with:
- both order books' best bid and ask;
- volumes and resolution dates;
- a `trusted` flag.

`trusted` is true only when both venues are among Polymarket, Kalshi and Limitless, the three with deep, reliable order books. Myriad and Opinion are logged but not trusted.

A GitHub Actions workflow runs the logger and commits the CSV back to the repo. It is scheduled every 30 minutes, but GitHub delays and drops scheduled jobs, so the median gap between runs is 1.8 hours.

```
arb_logger.py             Fetches matched markets from PMXT and appends spreads to the CSV
analyze_spreads.py        Regenerates every number below from the CSV (no key, no network)
arb_opportunities.csv     The dataset: 43,000+ rows, one per spread per run
.github/workflows/        Scheduled logging run
```

All spreads are in **percentage points** of the $1 payout: 0.05 → 0.10 is a 5-point spread.

---

## Findings (23 June – 24 October 2026, 1,099 runs)

Reproduce these with `python analyze_spreads.py`.

**1. The biggest "arbitrage" between trusted venues was a data artefact.** The log contains apparent 99-point spreads between Limitless and Polymarket on World Cup winner markets. On inspection, Polymarket's book had **no bids at all** in those rows, and the sell price came through as $1.00. There was nobody to sell to. 59 rows have a price that no quote in the book supports, 34 of them between trusted venues. The analysis excludes them, which cuts the largest trusted spread from 99 to 41 points.

**2. Between trusted venues, spreads are usually too small to trade.** On 1,186 quote-backed observations, the median spread is 0.5 points, 91% are 2 points or under, and only 2.3% exceed 5 points. Fees are not modelled, so these are upper bounds.

**3. Large spreads are almost entirely a small-venue phenomenon.** 99% of spreads above 5 points involve Myriad or Opinion. For example, during development (21 June, before automated logging began) Myriad showed AOC jumping to 100% with no corresponding move on Polymarket or Kalshi. That looked like an oracle or pricing failure, not information.

**4. Real trusted opportunities exist, but they are few and short-lived.** Across four months there were 24 distinct trusted spreads above 2 points. 13 of them were seen on a single day only. The most persistent was AOC for the 2028 Democratic nomination, Kalshi versus Limitless, at a median of 2.5 points over 18 runs between August and October.

**5. The matcher's confidence score is uninformative.** Every row is labelled `identity` with confidence `1`, so it cannot be used to filter mismatched markets. Whether two listings resolve on identical terms has to be checked by hand. The large "Who will win the next presidential election?" spread is one to treat with suspicion.

### What these numbers do not show

- **No fees, gas or capital lock-up.** Capital tied up in a 2028 market for two years has a real cost, and a 2.5-point spread on a long-dated contract is a low annualised return.
- **Top of book only.** The size available at the quoted price is not recorded, so even a real spread may only be good for a few dollars.
- **Gaps between runs.** Opportunities lasting less than about two hours are mostly invisible.

---

## Running it

The analysis needs only the standard library:

```bash
python analyze_spreads.py
python analyze_spreads.py --top 20     # more persistent opportunities
```

The logger needs a PMXT API key:

```bash
pip install -r requirements.txt
export PMXT_API_KEY=...
python arb_logger.py
```

To run it on a schedule in your own fork, add `PMXT_API_KEY` to the repository's Actions secrets.

---

## How this was built

I designed the monitor and built it with AI assistants, first Google Gemini and then Claude as a pair programmer. Examples of the Claude work include adding retry logic with back-off when the PMXT API proved unstable, and working out why some venues produced implausible spreads. The October audit was done with Claude Code working directly on the repo. It found the unbacked $1.00 sell prices behind the largest spreads, removed a line that printed part of the API key into public logs, and wrote `analyze_spreads.py` so every finding above can be regenerated from the raw data.
