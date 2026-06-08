# Trader Performance vs Market Sentiment

Primetrade.ai Round-0 Task — analysis of the relationship between Hyperliquid trader performance and Bitcoin market sentiment.

## Summary

Across 32 traders and 211,224 trades (May 2023 – May 2025), three findings:

1. **Average PnL is 2.7× higher during Fear than during Extreme Greed** ($126 vs $46 per trade, p < 0.001).
2. **Top 5 traders are aggressively contrarian** — 97% long during Extreme Fear, only 12% long during Extreme Greed. Bottom 5 are perma-short and lose money on rebounds.
3. **Daily PnL is negatively correlated with sentiment score** (Spearman ρ = −0.17, p < 0.001).

Strategy implication: contrarian positioning conditioned on sentiment explains most of the performance dispersion in this dataset.

## Repository Structure

```
.
├── analysis.ipynb              Full analysis notebook (run top-to-bottom)
├── analysis.py                 Same analysis as a Python script
├── report.md                   Standalone markdown report
├── report.pdf                  Exported PDF report (submit this)
├── data/
│   ├── historical_data.csv     Hyperliquid trader data
│   └── fear_greed_index.csv    Crypto Fear & Greed Index
├── figures/                    All generated charts (PNG)
└── trader_rankings.csv         Per-trader PnL ranking output
```

## How to Run

```bash
pip install pandas numpy matplotlib seaborn scipy jupyter
jupyter notebook analysis.ipynb
```

Or run the script directly:
```bash
python analysis.py
```

## Tech Stack

- Python 3.11
- pandas, numpy for data manipulation
- matplotlib, seaborn for visualization
- scipy.stats for hypothesis testing

## Notes

- The task description mentions a `leverage` column, but it is **not present** in the provided CSV. Leverage-conditioned analysis is therefore excluded from this report.
- The `event` column referenced in the task is called `Direction` in the actual CSV (values: `Open Long`, `Close Long`, `Open Short`, `Close Short`, etc.).
- Realized PnL is only populated on close events (~40% of rows); open events are excluded from PnL analysis.

## Author

Shivam Tiwari (Forge) — June 2026
