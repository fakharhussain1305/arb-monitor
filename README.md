# arb-monitor
# Cross-Platform Prediction Market Arbitrage Monitor

Logs arbitrage opportunities across Polymarket, Kalshi, and Limitless 
every 30 minutes using the PMXT unified API.

## Findings
- Large apparent spreads (>5%) are consistently explained by platform 
  quality issues on smaller venues (Myriad, Opinion)
- Between trusted platforms, spreads are typically under 2% and 
  compress to near-zero after fees
- Documented a live Myriad oracle failure (2026-06-21) where AOC 
  jumped to 100% with no corresponding move on Polymarket or Kalshi

## Setup
Add `PMXT_API_KEY` to repository secrets. Logger runs automatically 
every 30 minutes via GitHub Actions and commits results to 
`arb_opportunities.csv`.
