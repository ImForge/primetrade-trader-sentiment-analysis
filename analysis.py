"""
Primetrade.ai Round-0 Task
Trader Performance vs Market Sentiment Analysis

Datasets:
- Hyperliquid historical trader data (32 traders, 211k trades, May 2023 - May 2025)
- Crypto Fear & Greed Index (daily sentiment, 0-100 scale + 5 classifications)

Author: Shivam Tiwari (Forge)
Date: June 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# CONFIG
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'

SENTIMENT_ORDER = ['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed']
SENTIMENT_COLORS = {
    'Extreme Fear': '#8B0000', 'Fear': '#CD5C5C', 'Neutral': '#808080',
    'Greed': '#90EE90', 'Extreme Greed': '#006400'
}

BASE = Path(__file__).parent
DATA_DIR = BASE / 'data'
FIG_DIR = BASE / 'figures'
FIG_DIR.mkdir(exist_ok=True)


def load_and_merge():
    """Load both datasets, parse dates, merge on date, split into closes/opens."""
    trades = pd.read_csv(DATA_DIR / 'historical_data.csv')
    sentiment = pd.read_csv(DATA_DIR / 'fear_greed_index.csv')

    trades['datetime'] = pd.to_datetime(trades['Timestamp IST'], format='%d-%m-%Y %H:%M')
    trades['date'] = trades['datetime'].dt.date
    sentiment['date'] = pd.to_datetime(sentiment['date']).dt.date

    df = trades.merge(sentiment[['date', 'value', 'classification']], on='date', how='left')
    df = df.rename(columns={'value': 'fg_value', 'classification': 'sentiment'})

    unmatched = df['sentiment'].isna().sum()
    print(f"Loaded {len(df):,} trades from {df['Account'].nunique()} accounts")
    print(f"Rows without sentiment match: {unmatched} (dropped)")
    df = df.dropna(subset=['sentiment'])
    df['sentiment'] = pd.Categorical(df['sentiment'], categories=SENTIMENT_ORDER, ordered=True)

    closes = df[df['Direction'].str.contains('Close', case=False, na=False)].copy()
    closes['win'] = closes['Closed PnL'] > 0
    opens = df[df['Direction'].str.contains('Open', case=False, na=False)].copy()
    opens['position_type'] = opens['Direction'].apply(
        lambda x: 'Long' if 'Long' in x else ('Short' if 'Short' in x else 'Other'))
    return df, closes, opens


def insight_1_win_rate(closes):
    win_rate = closes.groupby('sentiment', observed=True)['win'].agg(['mean', 'count'])
    win_rate['mean'] = win_rate['mean'] * 100
    win_rate.columns = ['Win Rate %', 'Trade Count']
    print("\n=== INSIGHT 1: WIN RATE BY SENTIMENT ===")
    print(win_rate.round(2))

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [SENTIMENT_COLORS[s] for s in win_rate.index]
    bars = ax.bar(win_rate.index.astype(str), win_rate['Win Rate %'], color=colors, edgecolor='black')
    ax.axhline(50, color='black', linestyle='--', alpha=0.5, label='50% (coin flip)')
    ax.set_ylabel('Win Rate (%)', fontsize=12)
    ax.set_xlabel('Market Sentiment', fontsize=12)
    ax.set_title('Trader Win Rate by Market Sentiment', fontsize=14, fontweight='bold')
    ax.legend()
    for bar, val, n in zip(bars, win_rate['Win Rate %'], win_rate['Trade Count']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{val:.1f}%\n(n={n:,})", ha='center', fontsize=10)
    plt.tight_layout()
    plt.savefig(FIG_DIR / '01_win_rate_by_sentiment.png')
    plt.close()
    return win_rate


def insight_2_pnl(closes):
    pnl_summary = closes.groupby('sentiment', observed=True)['Closed PnL'].agg(['mean', 'median', 'sum', 'count'])
    pnl_summary.columns = ['Mean PnL ($)', 'Median PnL ($)', 'Total PnL ($)', 'Trade Count']
    print("\n=== INSIGHT 2: PNL BY SENTIMENT ===")
    print(pnl_summary.round(2))

    fear_pnl = closes[closes['sentiment'].isin(['Extreme Fear', 'Fear'])]['Closed PnL']
    greed_pnl = closes[closes['sentiment'].isin(['Greed', 'Extreme Greed'])]['Closed PnL']
    u_stat, p_val = stats.mannwhitneyu(fear_pnl, greed_pnl, alternative='two-sided')
    print(f"\nMann-Whitney U (Fear vs Greed PnL): U={u_stat:,.0f}, p={p_val:.2e}")
    print(f"Fear mean: ${fear_pnl.mean():.2f}  |  Greed mean: ${greed_pnl.mean():.2f}")

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    colors = [SENTIMENT_COLORS[s] for s in pnl_summary.index]
    bars = axes[0].bar(pnl_summary.index.astype(str), pnl_summary['Mean PnL ($)'], color=colors, edgecolor='black')
    axes[0].axhline(0, color='black', linewidth=0.8)
    axes[0].set_ylabel('Mean PnL per Trade ($)', fontsize=12)
    axes[0].set_xlabel('Market Sentiment', fontsize=12)
    axes[0].set_title('Average Realized PnL per Closed Trade', fontsize=13, fontweight='bold')
    axes[0].set_ylim(0, pnl_summary['Mean PnL ($)'].max() * 1.15)
    for bar, val in zip(bars, pnl_summary['Mean PnL ($)']):
        axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, f"${val:.1f}", ha='center', fontsize=10)

    bars = axes[1].bar(pnl_summary.index.astype(str), pnl_summary['Total PnL ($)']/1e6, color=colors, edgecolor='black')
    axes[1].axhline(0, color='black', linewidth=0.8)
    axes[1].set_ylabel('Total PnL ($ Millions)', fontsize=12)
    axes[1].set_xlabel('Market Sentiment', fontsize=12)
    axes[1].set_title('Total Realized PnL by Sentiment Regime', fontsize=13, fontweight='bold')
    axes[1].set_ylim(0, (pnl_summary['Total PnL ($)']/1e6).max() * 1.15)
    for bar, val in zip(bars, pnl_summary['Total PnL ($)']/1e6):
        axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, f"${val:.2f}M", ha='center', fontsize=10)
    plt.tight_layout()
    plt.savefig(FIG_DIR / '02_pnl_by_sentiment.png')
    plt.close()
    return pnl_summary


def insight_3_bias(opens):
    bias = opens.groupby(['sentiment', 'position_type'], observed=True).size().unstack(fill_value=0)
    bias['Long %'] = 100 * bias['Long'] / (bias['Long'] + bias['Short'])
    print("\n=== INSIGHT 3: LONG/SHORT BIAS ===")
    print(bias.round(2))

    fig, ax = plt.subplots(figsize=(11, 6.5))
    x = np.arange(len(SENTIMENT_ORDER))
    width = 0.35
    longs = [bias.loc[s, 'Long'] if s in bias.index else 0 for s in SENTIMENT_ORDER]
    shorts = [bias.loc[s, 'Short'] if s in bias.index else 0 for s in SENTIMENT_ORDER]
    ax.bar(x - width/2, longs, width, label='Long Opens', color='#2E8B57', edgecolor='black')
    ax.bar(x + width/2, shorts, width, label='Short Opens', color='#B22222', edgecolor='black')
    ax.set_xticks(x); ax.set_xticklabels(SENTIMENT_ORDER)
    ax.set_ylabel('Number of Position Opens', fontsize=12)
    ax.set_xlabel('Market Sentiment', fontsize=12)
    ax.set_title('Long vs Short Position Opens by Sentiment', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right')
    ax.set_ylim(0, max(longs + shorts) * 1.2)
    for i, s in enumerate(SENTIMENT_ORDER):
        if s in bias.index:
            pct = bias.loc[s, 'Long %']
            color = '#2E8B57' if pct >= 50 else '#B22222'
            ax.text(i, max(longs[i], shorts[i]) + max(longs+shorts)*0.04,
                    f"{pct:.0f}% Long", ha='center', fontsize=11, fontweight='bold', color=color)
    plt.tight_layout()
    plt.savefig(FIG_DIR / '03_long_short_bias.png')
    plt.close()
    return bias


def insight_4_top_vs_bottom(closes, opens):
    trader_pnl = closes.groupby('Account')['Closed PnL'].agg(['sum', 'count', 'mean'])
    trader_pnl.columns = ['Total PnL', 'Trade Count', 'Mean PnL']
    trader_pnl = trader_pnl.sort_values('Total PnL', ascending=False)
    trader_pnl.to_csv(BASE / 'trader_rankings.csv')

    top5 = trader_pnl.head(5).index.tolist()
    bottom5 = trader_pnl.tail(5).index.tolist()

    print("\n=== INSIGHT 4: TOP vs BOTTOM TRADERS ===")
    print(f"Top 5 total PnL: ${trader_pnl.head(5)['Total PnL'].sum():,.0f}")
    print(f"Bottom 5 total PnL: ${trader_pnl.tail(5)['Total PnL'].sum():,.0f}")
    print(f"All 32 total PnL: ${trader_pnl['Total PnL'].sum():,.0f}")

    def stats_by_group(accounts, label):
        sub = closes[closes['Account'].isin(accounts)].copy()
        out = sub.groupby('sentiment', observed=True).agg(win_rate=('win', 'mean'), avg_pnl=('Closed PnL', 'mean'))
        out['win_rate'] *= 100
        out['group'] = label
        return out.reset_index()

    top_stats = stats_by_group(top5, 'Top 5')
    bot_stats = stats_by_group(bottom5, 'Bottom 5')
    combined = pd.concat([top_stats, bot_stats])

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    for i, (col, ylabel, title, baseline) in enumerate([
        ('win_rate', 'Win Rate (%)', 'Win Rate by Sentiment', 50),
        ('avg_pnl', 'Average PnL per Trade ($)', 'Avg PnL by Sentiment', 0)]):
        pivot = combined.pivot(index='sentiment', columns='group', values=col).reindex(SENTIMENT_ORDER)
        pivot = pivot[['Top 5', 'Bottom 5']]
        pivot.plot(kind='bar', ax=axes[i], color=['#2E8B57', '#B22222'], edgecolor='black')
        axes[i].axhline(baseline, color='black', linestyle='--', alpha=0.5)
        axes[i].set_ylabel(ylabel, fontsize=12)
        axes[i].set_xlabel('Market Sentiment', fontsize=12)
        axes[i].set_title(f'Top 5 vs Bottom 5 Traders: {title}', fontsize=13, fontweight='bold')
        axes[i].set_xticklabels(SENTIMENT_ORDER, rotation=0)
        axes[i].legend(title='Trader Group')
    axes[0].set_ylim(0, 110)
    plt.tight_layout()
    plt.savefig(FIG_DIR / '04_top_vs_bottom_traders.png')
    plt.close()

    # Headline contrarian chart
    def get_ls_pct(opens_df):
        g = opens_df.groupby('sentiment', observed=True)['position_type'].value_counts().unstack(fill_value=0)
        g['Long %'] = 100 * g['Long'] / (g['Long'] + g['Short'])
        return g['Long %'].reindex(SENTIMENT_ORDER)

    top_ls = get_ls_pct(opens[opens['Account'].isin(top5)])
    bot_ls = get_ls_pct(opens[opens['Account'].isin(bottom5)])

    print("\nLong-bias by sentiment (Top 5 vs Bottom 5):")
    print(pd.DataFrame({'Top 5 %Long': top_ls, 'Bottom 5 %Long': bot_ls}).round(1))

    fig, ax = plt.subplots(figsize=(11, 6.5))
    x = np.arange(len(SENTIMENT_ORDER))
    width = 0.35
    ax.bar(x - width/2, top_ls.values, width, label='Top 5 Traders', color='#2E8B57', edgecolor='black')
    ax.bar(x + width/2, bot_ls.values, width, label='Bottom 5 Traders', color='#B22222', edgecolor='black')
    ax.axhline(50, color='black', linestyle='--', alpha=0.5, label='50% (Long/Short balance)')
    ax.set_xticks(x); ax.set_xticklabels(SENTIMENT_ORDER)
    ax.set_ylabel('% Long Positions (vs Short)', fontsize=12)
    ax.set_xlabel('Market Sentiment', fontsize=12)
    ax.set_title('The Contrarian Pattern: Top vs Bottom Traders\n% of Position Opens that are LONG',
                 fontsize=13, fontweight='bold', pad=15)
    ax.set_ylim(0, 110); ax.legend(loc='upper right')
    for i, (t, b) in enumerate(zip(top_ls.values, bot_ls.values)):
        ax.text(i - width/2, t + 2, f"{t:.0f}%", ha='center', fontsize=10, fontweight='bold', color='#2E8B57')
        ax.text(i + width/2, b + 2, f"{b:.0f}%", ha='center', fontsize=10, fontweight='bold', color='#B22222')
    plt.tight_layout()
    plt.savefig(FIG_DIR / '06_contrarian_pattern.png')
    plt.close()
    return trader_pnl


def insight_5_correlation(closes):
    daily = closes.groupby('date').agg(
        total_pnl=('Closed PnL', 'sum'),
        fg_value=('fg_value', 'first'),
        sentiment=('sentiment', 'first')
    ).reset_index()

    r_p, p_p = stats.pearsonr(daily['fg_value'], daily['total_pnl'])
    r_s, p_s = stats.spearmanr(daily['fg_value'], daily['total_pnl'])
    print("\n=== INSIGHT 5: DAILY PNL vs F&G VALUE ===")
    print(f"Pearson:  r = {r_p:.4f} (p = {p_p:.4f})")
    print(f"Spearman: r = {r_s:.4f} (p = {p_s:.4f})")

    fig, ax = plt.subplots(figsize=(11, 6))
    scatter = ax.scatter(daily['fg_value'], daily['total_pnl'], c=daily['fg_value'],
                         cmap='RdYlGn', alpha=0.6, edgecolor='black', s=40)
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_xlabel('Fear & Greed Index Value (0=Extreme Fear, 100=Extreme Greed)', fontsize=12)
    ax.set_ylabel('Total Daily PnL ($)', fontsize=12)
    ax.set_title(f'Daily Trader PnL vs Market Sentiment Value (Spearman r={r_s:.3f})',
                 fontsize=13, fontweight='bold')
    plt.colorbar(scatter, ax=ax, label='F&G Value')
    plt.tight_layout()
    plt.savefig(FIG_DIR / '05_daily_pnl_vs_fg_value.png')
    plt.close()

    daily['cum_pnl'] = daily['total_pnl'].cumsum()
    daily['date_dt'] = pd.to_datetime(daily['date'])
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(daily['date_dt'], daily['cum_pnl']/1e6, color='black', linewidth=2)
    ax.fill_between(daily['date_dt'], 0, daily['cum_pnl']/1e6, alpha=0.1, color='black')
    ax.set_ylabel('Cumulative PnL ($ Millions)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_title('Cumulative Trader PnL Over Time (All 32 Traders Combined)', fontsize=13, fontweight='bold')
    ax.axhline(0, color='red', linewidth=0.8, alpha=0.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIG_DIR / '07_cumulative_pnl.png')
    plt.close()
    return daily


if __name__ == '__main__':
    print("=" * 60)
    print("Primetrade.ai Round-0 Analysis")
    print("=" * 60)
    df, closes, opens = load_and_merge()
    insight_1_win_rate(closes)
    insight_2_pnl(closes)
    insight_3_bias(opens)
    insight_4_top_vs_bottom(closes, opens)
    insight_5_correlation(closes)
    print("\n" + "=" * 60)
    print("Analysis complete. See figures/ for charts.")
    print("=" * 60)
