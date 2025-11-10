"""
Reporter Module
===============
Automated daily/weekly/monthly reporting.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

from journal.database import TradeDatabase
from journal.analyzer import TradeAnalyzer


class Reporter:
    """
    Automated reporting system.

    Generates:
    - Daily summaries
    - Weekly reviews
    - Monthly performance reports
    """

    def __init__(self, db: TradeDatabase):
        """
        Initialize reporter.

        Args:
            db: TradeDatabase instance
        """
        self.db = db
        self.analyzer = TradeAnalyzer(db)

    def daily_summary(
        self,
        date: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> str:
        """
        Generate daily summary report.

        Args:
            date: Date (YYYY-MM-DD), defaults to today
            strategy: Filter by strategy

        Returns:
            Formatted daily summary
        """
        if date is None:
            date = datetime.now().date().isoformat()

        # Get trades for the day
        trades_df = self.db.get_trades(
            strategy=strategy,
            start_date=date,
            end_date=date
        )

        report = []
        report.append("\n" + "="*70)
        report.append(f"DAILY SUMMARY - {date}")
        if strategy:
            report.append(f"Strategy: {strategy}")
        report.append("="*70 + "\n")

        if len(trades_df) == 0:
            report.append("No trades today.\n")
            return "\n".join(report)

        # Calculate metrics
        num_trades = len(trades_df)
        num_wins = len(trades_df[trades_df['pnl'] > 0])
        num_losses = len(trades_df[trades_df['pnl'] <= 0])
        win_rate = (num_wins / num_trades * 100) if num_trades > 0 else 0

        total_pnl = trades_df['pnl'].sum()
        avg_pnl = trades_df['pnl_pct'].mean()

        best_trade = trades_df.loc[trades_df['pnl_pct'].idxmax()] if num_trades > 0 else None
        worst_trade = trades_df.loc[trades_df['pnl_pct'].idxmin()] if num_trades > 0 else None

        # Format report
        report.append(f"Trades Today:       {num_trades}")
        report.append(f"Winners:            {num_wins}")
        report.append(f"Losers:             {num_losses}")
        report.append(f"Win Rate:           {win_rate:.2f}%")
        report.append(f"\nTotal P&L:          ${total_pnl:.2f}")
        report.append(f"Average P&L:        {avg_pnl:.2f}%")

        if best_trade is not None:
            report.append(f"\nBest Trade:")
            report.append(f"  Asset:            {best_trade['asset']}")
            report.append(f"  Direction:        {best_trade['direction']}")
            report.append(f"  P&L:              {best_trade['pnl_pct']:.2f}%")
            report.append(f"  Exit:             {best_trade['exit_reason']}")

        if worst_trade is not None:
            report.append(f"\nWorst Trade:")
            report.append(f"  Asset:            {worst_trade['asset']}")
            report.append(f"  Direction:        {worst_trade['direction']}")
            report.append(f"  P&L:              {worst_trade['pnl_pct']:.2f}%")
            report.append(f"  Exit:             {worst_trade['exit_reason']}")

        # Asset breakdown
        if 'asset' in trades_df.columns:
            report.append(f"\nBy Asset:")
            asset_summary = trades_df.groupby('asset').agg({
                'pnl': ['count', 'sum'],
                'pnl_pct': 'mean'
            }).round(2)
            for asset in asset_summary.index:
                count = asset_summary.loc[asset, ('pnl', 'count')]
                pnl = asset_summary.loc[asset, ('pnl', 'sum')]
                avg = asset_summary.loc[asset, ('pnl_pct', 'mean')]
                report.append(f"  {asset:20s} {count:>3.0f} trades | ${pnl:>8.2f} | {avg:>6.2f}%")

        report.append("\n" + "="*70 + "\n")

        return "\n".join(report)

    def weekly_review(
        self,
        strategy: Optional[str] = None,
        weeks_ago: int = 0
    ) -> str:
        """
        Generate weekly review.

        Args:
            strategy: Filter by strategy
            weeks_ago: 0 for current week, 1 for last week, etc.

        Returns:
            Formatted weekly review
        """
        # Calculate week dates
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday() + 7 * weeks_ago)
        end_of_week = start_of_week + timedelta(days=6)

        # Get trades
        trades_df = self.db.get_trades(
            strategy=strategy,
            start_date=start_of_week.isoformat(),
            end_date=end_of_week.isoformat()
        )

        report = []
        report.append("\n" + "="*70)
        report.append(f"WEEKLY REVIEW - Week of {start_of_week}")
        if strategy:
            report.append(f"Strategy: {strategy}")
        report.append("="*70 + "\n")

        if len(trades_df) == 0:
            report.append("No trades this week.\n")
            return "\n".join(report)

        # Weekly metrics
        num_trades = len(trades_df)
        num_wins = len(trades_df[trades_df['pnl'] > 0])
        win_rate = (num_wins / num_trades * 100) if num_trades > 0 else 0

        total_pnl = trades_df['pnl'].sum()
        avg_pnl = trades_df['pnl_pct'].mean()

        # Winners/losers
        winners = trades_df[trades_df['pnl'] > 0]
        losers = trades_df[trades_df['pnl'] <= 0]

        avg_win = winners['pnl_pct'].mean() if len(winners) > 0 else 0
        avg_loss = losers['pnl_pct'].mean() if len(losers) > 0 else 0

        profit_factor = (
            winners['pnl'].sum() / abs(losers['pnl'].sum())
            if len(losers) > 0 and losers['pnl'].sum() != 0
            else 0
        )

        # Format report
        report.append(f"Total Trades:       {num_trades}")
        report.append(f"Win Rate:           {win_rate:.2f}%")
        report.append(f"Profit Factor:      {profit_factor:.2f}")
        report.append(f"\nTotal P&L:          ${total_pnl:.2f}")
        report.append(f"Average P&L:        {avg_pnl:.2f}%")
        report.append(f"Average Win:        {avg_win:.2f}%")
        report.append(f"Average Loss:       {avg_loss:.2f}%")

        # Daily breakdown
        report.append(f"\nDaily Breakdown:")
        trades_df['date'] = pd.to_datetime(trades_df['entry_time']).dt.date
        daily = trades_df.groupby('date').agg({
            'pnl': ['count', 'sum'],
            'pnl_pct': 'mean'
        }).round(2)

        for date in daily.index:
            count = daily.loc[date, ('pnl', 'count')]
            pnl = daily.loc[date, ('pnl', 'sum')]
            avg = daily.loc[date, ('pnl_pct', 'mean')]
            day_name = pd.to_datetime(date).strftime('%A')
            report.append(f"  {date} ({day_name:9s}) | {count:>3.0f} trades | ${pnl:>8.2f} | {avg:>6.2f}%")

        # Best and worst days
        best_day = daily.loc[daily[('pnl', 'sum')].idxmax()]
        worst_day = daily.loc[daily[('pnl', 'sum')].idxmin()]

        report.append(f"\nBest Day:           {daily[('pnl', 'sum')].idxmax()} (${best_day[('pnl', 'sum')]:.2f})")
        report.append(f"Worst Day:          {daily[('pnl', 'sum')].idxmin()} (${worst_day[('pnl', 'sum')]:.2f})")

        report.append("\n" + "="*70 + "\n")

        return "\n".join(report)

    def monthly_report(
        self,
        strategy: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> str:
        """
        Generate monthly performance report.

        Args:
            strategy: Filter by strategy
            year: Year (defaults to current)
            month: Month (defaults to current)

        Returns:
            Formatted monthly report
        """
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month

        # Calculate month dates
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        # Get trades
        trades_df = self.db.get_trades(
            strategy=strategy,
            start_date=start_date,
            end_date=end_date
        )

        month_name = datetime(year, month, 1).strftime('%B %Y')

        report = []
        report.append("\n" + "="*70)
        report.append(f"MONTHLY REPORT - {month_name}")
        if strategy:
            report.append(f"Strategy: {strategy}")
        report.append("="*70 + "\n")

        if len(trades_df) == 0:
            report.append("No trades this month.\n")
            return "\n".join(report)

        # Monthly metrics
        num_trades = len(trades_df)
        num_wins = len(trades_df[trades_df['pnl'] > 0])
        win_rate = (num_wins / num_trades * 100) if num_trades > 0 else 0

        total_pnl = trades_df['pnl'].sum()
        avg_pnl = trades_df['pnl_pct'].mean()

        winners = trades_df[trades_df['pnl'] > 0]
        losers = trades_df[trades_df['pnl'] <= 0]

        # Format report
        report.append("OVERVIEW")
        report.append("-" * 70)
        report.append(f"Total Trades:       {num_trades}")
        report.append(f"Winners:            {len(winners)}")
        report.append(f"Losers:             {len(losers)}")
        report.append(f"Win Rate:           {win_rate:.2f}%")
        report.append(f"\nTotal P&L:          ${total_pnl:.2f}")
        report.append(f"Average P&L:        {avg_pnl:.2f}%")

        # Risk-adjusted metrics (using analyzer)
        report.append(f"\nRISK-ADJUSTED METRICS")
        report.append("-" * 70)

        returns = trades_df['pnl_pct'] / 100
        sharpe = (returns.mean() / returns.std()) * (252 ** 0.5) if returns.std() > 0 else 0

        report.append(f"Sharpe Ratio:       {sharpe:.2f}")

        profit_factor = (
            winners['pnl'].sum() / abs(losers['pnl'].sum())
            if len(losers) > 0 and losers['pnl'].sum() != 0
            else 0
        )
        report.append(f"Profit Factor:      {profit_factor:.2f}")

        # Weekly breakdown
        report.append(f"\nWEEKLY BREAKDOWN")
        report.append("-" * 70)

        trades_df['week'] = pd.to_datetime(trades_df['entry_time']).dt.isocalendar().week
        weekly = trades_df.groupby('week').agg({
            'pnl': ['count', 'sum'],
            'pnl_pct': 'mean'
        }).round(2)

        for week in weekly.index:
            count = weekly.loc[week, ('pnl', 'count')]
            pnl = weekly.loc[week, ('pnl', 'sum')]
            avg = weekly.loc[week, ('pnl_pct', 'mean')]
            report.append(f"  Week {week:2.0f} | {count:>3.0f} trades | ${pnl:>8.2f} | {avg:>6.2f}%")

        # Asset performance
        if 'asset' in trades_df.columns:
            report.append(f"\nPERFORMANCE BY ASSET")
            report.append("-" * 70)

            asset_perf = trades_df.groupby('asset').agg({
                'pnl': ['count', 'sum'],
                'pnl_pct': 'mean'
            }).round(2)

            # Sort by total P&L
            asset_perf = asset_perf.sort_values(('pnl', 'sum'), ascending=False)

            for asset in asset_perf.index:
                count = asset_perf.loc[asset, ('pnl', 'count')]
                pnl = asset_perf.loc[asset, ('pnl', 'sum')]
                avg = asset_perf.loc[asset, ('pnl_pct', 'mean')]
                report.append(f"  {asset:20s} | {count:>3.0f} trades | ${pnl:>8.2f} | {avg:>6.2f}%")

        report.append("\n" + "="*70 + "\n")

        return "\n".join(report)

    def export_report_to_file(
        self,
        report: str,
        filename: Optional[str] = None,
        output_dir: str = "reports"
    ):
        """
        Save report to file.

        Args:
            report: Report string
            filename: Output filename (auto-generated if None)
            output_dir: Output directory
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.txt"

        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w') as f:
            f.write(report)

        print(f"✓ Report saved to {filepath}")
