cat > ~/Downloads/arb_logger_final.py << 'EOF'
import pmxt
import csv
import os
from datetime import datetime, timezone

PMXT_KEY  = os.environ.get("PMXT_API_KEY")
if not PMXT_KEY:
    raise ValueError("PMXT_API_KEY environment variable not set")
LOG_FILE  = "arb_opportunities.csv"

TRUSTED   = {'polymarket', 'kalshi', 'limitless'}
FIELDS    = [
    'timestamp', 'title', 'buy_venue', 'sell_venue',
    'buy_price', 'sell_price', 'spread_pct',
    'confidence', 'relation',
    'bid_a', 'ask_a', 'bid_b', 'ask_b',
    'volume_a', 'volume_b', 'resolution_date',
    'market_id_a', 'market_id_b', 'trusted'
]

router    = pmxt.Router(pmxt_api_key=PMXT_KEY)
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

try:
    opps = router.fetch_arbitrage(limit=100)
except Exception as e:
    print(f"[{timestamp}] Fetch error: {e}")
    raise

file_exists = os.path.isfile(LOG_FILE)
logged = 0

with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    if not file_exists:
        writer.writeheader()

    for opp in sorted(opps, key=lambda x: x.spread, reverse=True):
        if opp.spread <= 0:
            continue
        is_trusted = (opp.buy_venue in TRUSTED and opp.sell_venue in TRUSTED)
        writer.writerow({
            'timestamp':       timestamp,
            'title':           opp.market_a.title[:80],
            'buy_venue':       opp.buy_venue,
            'sell_venue':      opp.sell_venue,
            'buy_price':       round(opp.buy_price, 5),
            'sell_price':      round(opp.sell_price, 5),
            'spread_pct':      round(opp.spread * 100, 4),
            'confidence':      opp.confidence,
            'relation':        opp.relation,
            'bid_a':           opp.market_a.yes.best_bid,
            'ask_a':           opp.market_a.yes.best_ask,
            'bid_b':           opp.market_b.yes.best_bid,
            'ask_b':           opp.market_b.yes.best_ask,
            'volume_a':        round(opp.market_a.volume, 2),
            'volume_b':        round(opp.market_b.volume, 2),
            'resolution_date': str(opp.market_a.resolution_date),
            'market_id_a':     opp.market_a.market_id,
            'market_id_b':     opp.market_b.market_id,
            'trusted':         is_trusted,
        })
        logged += 1

trusted_count = sum(
    1 for o in opps
    if o.buy_venue in TRUSTED
    and o.sell_venue in TRUSTED
    and o.spread > 0
)

print(f"[{timestamp}] Total: {logged} | Trusted: {trusted_count}")
for opp in sorted(opps, key=lambda x: x.spread, reverse=True)[:3]:
    if opp.spread > 0:
        trusted_flag = "✓" if (
            opp.buy_venue in TRUSTED and opp.sell_venue in TRUSTED
        ) else "✗"
        print(f"  {trusted_flag} {opp.spread*100:.2f}% | "
              f"{opp.buy_venue}->{opp.sell_venue} | "
              f"{opp.market_a.title[:45]}")
EOF
python3 ~/Downloads/arb_logger_final.py
