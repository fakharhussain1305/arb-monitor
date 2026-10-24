"""
analyze_spreads.py
------------------
Regenerates the README's findings from arb_opportunities.csv.

Standard library only, no API key, no network:

    python analyze_spreads.py            # summary
    python analyze_spreads.py --top 20   # longer list of persistent spreads

Every number in the README's Findings section comes from this script.
"""

import argparse
import csv
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime

LOG_FILE = "arb_opportunities.csv"
QUOTE_TOLERANCE = 5e-4   # prices are logged rounded to 5 d.p.


def _num(value):
    return float(value) if value not in ("", None) else None


def _matches(quote, price):
    return quote is not None and abs(quote - price) < QUOTE_TOLERANCE


def is_quote_backed(row):
    """True if both legs are priced off a real resting quote.

    A spread is only executable if you can buy at someone's ask and sell into
    someone's bid. In some rows one book has no bids at all, and the sell
    price comes through as 1.0. Those rows look like 99-point arbitrage
    and are not: there is nobody to sell to.
    """
    bid_a, ask_a, bid_b, ask_b = (_num(row[k]) for k in ("bid_a", "ask_a", "bid_b", "ask_b"))
    buy, sell = float(row["buy_price"]), float(row["sell_price"])
    return ((_matches(ask_a, buy) or _matches(ask_b, buy))
            and (_matches(bid_a, sell) or _matches(bid_b, sell)))


def load(path=LOG_FILE):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["spread"] = float(r["spread_pct"])          # percentage points
        r["is_trusted"] = r["trusted"] == "True"
        r["backed"] = is_quote_backed(r)
    return rows


def distribution(spreads):
    s = sorted(spreads)
    n = len(s)
    return {
        "n": n,
        "median": statistics.median(s),
        "p90": s[int(0.9 * (n - 1))],
        "max": s[-1],
        "over_2": sum(x > 2 for x in s) / n,
        "over_5": sum(x > 5 for x in s) / n,
    }


def fmt(d):
    return (f"n={d['n']:>6}  median {d['median']:.2f}  p90 {d['p90']:.2f}  "
            f"max {d['max']:.1f}  >2pp {d['over_2']:5.1%}  >5pp {d['over_5']:5.1%}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--file", default=LOG_FILE)
    parser.add_argument("--top", type=int, default=8)
    args = parser.parse_args(argv)

    rows = load(args.file)
    runs = sorted({r["timestamp"] for r in rows})
    times = [datetime.fromisoformat(t) for t in runs]
    gaps = [(b - a).total_seconds() / 3600 for a, b in zip(times, times[1:])]

    print("=" * 78)
    print("CROSS-VENUE SPREAD LOG - SUMMARY  (spreads in percentage points)")
    print("=" * 78)
    print(f"Rows {len(rows)}  |  runs {len(runs)}  |  {runs[0][:10]} to {runs[-1][:10]}")
    if gaps:
        print(f"Gap between runs: median {statistics.median(gaps):.1f}h, max {max(gaps):.1f}h "
              f"(scheduled every 30 min; GitHub delays and drops scheduled jobs)")

    venues = Counter()
    for r in rows:
        venues[r["buy_venue"]] += 1
        venues[r["sell_venue"]] += 1
    print("Venue appearances: " + ", ".join(f"{v} {n}" for v, n in venues.most_common()))

    unbacked = [r for r in rows if not r["backed"]]
    print(f"\n1. Data quality: {len(unbacked)} rows have a price with no quote behind it")
    ub_t = [r for r in unbacked if r["is_trusted"]]
    if ub_t:
        print(f"   {len(ub_t)} are between trusted venues, max apparent spread "
              f"{max(r['spread'] for r in ub_t):.1f}pp; these are excluded below")

    backed = [r for r in rows if r["backed"]]
    trusted = [r for r in backed if r["is_trusted"]]
    other = [r for r in backed if not r["is_trusted"]]
    print("\n2. Spread distribution, quote-backed rows only")
    print(f"   Trusted pairs (Polymarket/Kalshi/Limitless)  {fmt(distribution([r['spread'] for r in trusted]))}")
    print(f"   Any pair involving another venue            {fmt(distribution([r['spread'] for r in other]))}")
    print(f"   Runs with at least one trusted spread: "
          f"{len({r['timestamp'] for r in trusted})} of {len(runs)}")

    wide = [r for r in backed if r["spread"] > 5]
    small = [r for r in wide if {r["buy_venue"], r["sell_venue"]} & {"myriad", "opinion"}]
    print(f"\n3. Of {len(wide)} spreads above 5pp, {len(small)} ({len(small) / len(wide):.0%}) "
          f"involve Myriad or Opinion")

    print(f"\n4. Most persistent trusted spreads above 2pp (seen in the most runs)")
    seen = defaultdict(list)
    for r in trusted:
        if r["spread"] > 2:
            seen[(r["title"], r["buy_venue"], r["sell_venue"])].append(r)
    ranked = sorted(seen.items(), key=lambda kv: -len(kv[1]))[: args.top]
    for (title, buy, sell), hits in ranked:
        med = statistics.median(h["spread"] for h in hits)
        print(f"   {len(hits):>3} runs  median {med:4.1f}pp  {buy:>9} -> {sell:<9}  "
              f"{hits[0]['timestamp'][:10]}..{hits[-1]['timestamp'][:10]}  {title[:42]}")
    print(f"   ({len(seen)} distinct trusted opportunities above 2pp in total)")

    fields = Counter((r["relation"], r["confidence"]) for r in rows)
    print(f"\n5. Matcher output: (relation, confidence) values seen: {dict(fields)}")
    print("   A single value means the field carries no information for filtering.")
    print("\nFees are not modelled. Spreads are before fees, gas and capital lock-up.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
