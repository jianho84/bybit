"""
Trade Analyzer
==============
Professional trade analysis tools.

Teaches you how to analyze your trading performance like a quant trader.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta

from journal.database import TradeDatabase


class TradeAnalyzer:
    """
    Comprehensive trade analysis tools.

    Analyzes:
    - Win/loss patterns
    - Time-of-day performance
    - Asset-specific edge
    - Strategy comparison
    - Drawdown analysis
    - Risk-adjusted returns
    """

    def __init__(self, db: TradeDatabase):
        """
        Initialize analyzer.

        Args:
            db: TradeDatabase instance
        """
        self.db = db

    # =========================================================================
    # BASIC ANALYSES
    # =========================================================================

    def analyze_win_loss_patterns(
        self,
        strategy: Optional[str] = None,
        days: int = 90
    ) -> Dict:
        """
        Analyze winning and losing trade patterns.

        This helps you understand:
        - What makes winners win
        - What makes losers lose
        - If you're cutting winners too early
        - If you're holding losers too long

        Args:
            strategy: Filter by strategy
            days: Number of days to analyze

        Returns:
            Analysis dictionary
        """
        # Get trades
        start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        trades_df = self.db.get_trades(strategy=strategy, start_date=start_date)

        if len(trades_df) == 0:
            return {'error': 'No trades found'}

        # Separate winners and losers
        winners = trades_df[trades_df['pnl'] > 0]
        losers = trades_df[trades_df['pnl'] <= 0]

        analysis = {
            'total_trades': len(trades_df),
            'num_winners': len(winners),
            'num_losers': len(losers),
            'win_rate': len(winners) / len(trades_df) * 100,

            # Winners analysis
            'avg_win_pct': winners['pnl_pct'].mean() if len(winners) > 0 else 0,
            'median_win_pct': winners['pnl_pct'].median() if len(winners) > 0 else 0,
            'avg_win_duration': winners['duration_hours'].mean() if len(winners) > 0 else 0,
            'best_win': winners['pnl_pct'].max() if len(winners) > 0 else 0,

            # Losers analysis
            'avg_loss_pct': losers['pnl_pct'].mean() if len(losers) > 0 else 0,
            'median_loss_pct': losers['pnl_pct'].median() if len(losers) > 0 else 0,
            'avg_loss_duration': losers['duration_hours'].mean() if len(losers) > 0 else 0,
            'worst_loss': losers['pnl_pct'].min() if len(losers) > 0 else 0,

            # Risk/reward
            'avg_rr_ratio': abs(winners['pnl_pct'].mean() / losers['pnl_pct'].mean()) if len(losers) > 0 and losers['pnl_pct'].mean() != 0 else 0,

            # Profit factor
            'profit_factor': winners['pnl'].sum() / abs(losers['pnl'].sum()) if len(losers) > 0 and losers['pnl'].sum() != 0 else 0,
        }

        # Exit reason breakdown
        if 'exit_reason' in trades_df.columns:
            exit_breakdown = trades_df.groupby('exit_reason').agg({
                'pnl_pct': ['count', 'mean', 'sum']
            })
            analysis['exit_reason_breakdown'] = exit_breakdown.to_dict()

        return analysis

    def analyze_time_of_day(
        self,
        strategy: Optional[str] = None,
        days: int = 90
    ) -> pd.DataFrame:
        """
        Analyze performance by hour of day.

        This shows you:
        - Which hours are most profitable
        - When you should avoid trading
        - If your strategy has time-of-day edge

        Args:
            strategy: Filter by strategy
            days: Number of days

        Returns:
            DataFrame with hourly statistics
        """
        start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        trades_df = self.db.get_trades(strategy=strategy, start_date=start_date)

        if len(trades_df) == 0:
            return pd.DataFrame()

        # Extract hour from entry time
        trades_df['hour'] = pd.to_datetime(trades_df['entry_time']).dt.hour

        # Group by hour
        hourly = trades_df.groupby('hour').agg({
            'pnl': ['count', 'sum', 'mean'],
            'pnl_pct': ['mean', 'std'],
            'duration_hours': 'mean'
        }).round(2)

        # Add win rate
        win_rate_by_hour = trades_df.groupby('hour').apply(
            lambda x: (x['pnl'] > 0).sum() / len(x) * 100
        )
        hourly['win_rate'] = win_rate_by_hour

        # Rename columns
        hourly.columns = [
            'num_trades', 'total_pnl', 'avg_pnl',
            'avg_pnl_pct', 'std_pnl_pct', 'avg_duration', 'win_rate'
        ]

        return hourly.sort_values('avg_pnl_pct', ascending=False)

    def analyze_by_asset(
        self,
        strategy: Optional[str] = None,
        days: int = 90
    ) -> pd.DataFrame:
        """
        Analyze performance by asset.

        This shows you:
        - Which coins your strategy works best on
        - Which to avoid
        - If you should specialize

        Args:
            strategy: Filter by strategy
            days: Number of days

        Returns:
            DataFrame with asset statistics
        """
        start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        trades_df = self.db.get_trades(strategy=strategy, start_date=start_date)

        if len(trades_df) == 0:
            return pd.DataFrame()

        # Group by asset
        by_asset = trades_df.groupby('asset').agg({
            'pnl': ['count', 'sum', 'mean'],
            'pnl_pct': ['mean', 'std'],
            'duration_hours': 'mean'
        }).round(2)

        # Win rate
        win_rate_by_asset = trades_df.groupby('asset').apply(
            lambda x: (x['pnl'] > 0).sum() / len(x) * 100
        )
        by_asset['win_rate'] = win_rate_by_asset

        # Profit factor
        profit_factor = trades_df.groupby('asset').apply(
            lambda x: x[x['pnl'] > 0]['pnl'].sum() / abs(x[x['pnl'] <= 0]['pnl'].sum())
            if x[x['pnl'] <= 0]['pnl'].sum() != 0 else 0
        )
        by_asset['profit_factor'] = profit_factor

        by_asset.columns = [
            'num_trades', 'total_pnl', 'avg_pnl',
            'avg_pnl_pct', 'std_pnl_pct', 'avg_duration',
            'win_rate', 'profit_factor'
        ]

        return by_asset.sort_values('avg_pnl_pct', ascending=False)

    def analyze_by_strategy(self, days: int = 90) -> pd.DataFrame:
        """
        Compare performance across strategies.

        This shows you:
        - Which strategy is best
        - Which needs improvement
        - Capital allocation decisions

        Args:
            days: Number of days

        Returns:
            DataFrame comparing strategies
        """
        start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        trades_df = self.db.get_trades(start_date=start_date)

        if len(trades_df) == 0:
            return pd.DataFrame()

        # Group by strategy
        by_strategy = trades_df.groupby('strategy').agg({
            'pnl': ['count', 'sum', 'mean'],
            'pnl_pct': ['mean', 'std'],
            'duration_hours': 'mean'
        }).round(2)

        # Win rate
        win_rate = trades_df.groupby('strategy').apply(
            lambda x: (x['pnl'] > 0).sum() / len(x) * 100
        )
        by_strategy['win_rate'] = win_rate

        # Sharpe ratio (simplified)
        sharpe = trades_df.groupby('strategy').apply(
            lambda x: (x['pnl_pct'].mean() / x['pnl_pct'].std()) * np.sqrt(252)
            if x['pnl_pct'].std() > 0 else 0
        )
        by_strategy['sharpe'] = sharpe

        # Profit factor
        profit_factor = trades_df.groupby('strategy').apply(
            lambda x: x[x['pnl'] > 0]['pnl'].sum() / abs(x[x['pnl'] <= 0]['pnl'].sum())
            if x[x['pnl'] <= 0]['pnl'].sum() != 0 else 0
        )
        by_strategy['profit_factor'] = profit_factor

        by_strategy.columns = [
            'num_trades', 'total_pnl', 'avg_pnl',
            'avg_pnl_pct', 'std_pnl_pct', 'avg_duration',
            'win_rate', 'sharpe', 'profit_factor'
        ]

        return by_strategy.sort_values('sharpe', ascending=False)

    # =========================================================================
    # ADVANCED ANALYSES
    # =========================================================================

    def analyze_consecutive_trades(
        self,
        strategy: Optional[str] = None,
        days: int = 90
    ) -> Dict:
        """
        Analyze consecutive wins/losses.

        This reveals:
        - If you're on tilt after losses
        - If you get overconfident after wins
        - Optimal time to take breaks

        Args:
            strategy: Filter by strategy
            days: Number of days

        Returns:
            Analysis of streaks
        """
        start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        trades_df = self.db.get_trades(strategy=strategy, start_date=start_date)

        if len(trades_df) == 0:
            return {'error': 'No trades found'}

        # Sort by time
        trades_df = trades_df.sort_values('entry_time')

        # Calculate streaks
        trades_df['is_win'] = trades_df['pnl'] > 0
        trades_df['streak'] = (trades_df['is_win'] != trades_df['is_win'].shift()).cumsum()

        # Analyze streaks
        streaks = trades_df.groupby('streak').agg({
            'is_win': ['first', 'count']
        })
        streaks.columns = ['is_win', 'length']

        win_streaks = streaks[streaks['is_win'] == True]['length']
        loss_streaks = streaks[streaks['is_win'] == False]['length']

        analysis = {
            'max_win_streak': win_streaks.max() if len(win_streaks) > 0 else 0,
            'avg_win_streak': win_streaks.mean() if len(win_streaks) > 0 else 0,
            'max_loss_streak': loss_streaks.max() if len(loss_streaks) > 0 else 0,
            'avg_loss_streak': loss_streaks.mean() if len(loss_streaks) > 0 else 0,
        }

        # Performance after wins vs losses
        trades_df['prev_is_win'] = trades_df['is_win'].shift(1)

        after_win = trades_df[trades_df['prev_is_win'] == True]['pnl_pct'].mean()
        after_loss = trades_df[trades_df['prev_is_win'] == False]['pnl_pct'].mean()

        analysis['avg_trade_after_win'] = after_win
        analysis['avg_trade_after_loss'] = after_loss
        analysis['revenge_trading'] = after_loss < after_win  # True if worse after losses

        return analysis

    def analyze_drawdowns(
        self,
        strategy: Optional[str] = None,
        days: int = 90
    ) -> Dict:
        """
        Analyze drawdown periods.

        This shows:
        - Max drawdown (worst peak-to-trough)
        - How long drawdowns last
        - Recovery time

        Args:
            strategy: Filter by strategy
            days: Number of days

        Returns:
            Drawdown analysis
        """
        start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        trades_df = self.db.get_trades(strategy=strategy, start_date=start_date)

        if len(trades_df) == 0:
            return {'error': 'No trades found'}

        # Sort by time
        trades_df = trades_df.sort_values('entry_time')

        # Calculate cumulative P&L
        trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()

        # Calculate running maximum
        trades_df['running_max'] = trades_df['cumulative_pnl'].expanding().max()

        # Calculate drawdown
        trades_df['drawdown'] = trades_df['cumulative_pnl'] - trades_df['running_max']

        # Find max drawdown
        max_dd_idx = trades_df['drawdown'].idxmin()
        max_dd = trades_df.loc[max_dd_idx, 'drawdown']

        # Find start of max drawdown (last peak before max dd)
        dd_start_idx = trades_df[:max_dd_idx]['running_max'].idxmax()

        # Duration
        dd_start_time = trades_df.loc[dd_start_idx, 'entry_time']
        dd_end_time = trades_df.loc[max_dd_idx, 'entry_time']
        dd_duration_days = (dd_end_time - dd_start_time).days

        # Recovery
        recovery_trades = trades_df[
            (trades_df.index > max_dd_idx) &
            (trades_df['cumulative_pnl'] >= trades_df.loc[dd_start_idx, 'cumulative_pnl'])
        ]

        if len(recovery_trades) > 0:
            recovery_time = (
                recovery_trades.iloc[0]['entry_time'] - dd_end_time
            ).days
            recovered = True
        else:
            recovery_time = None
            recovered = False

        return {
            'max_drawdown_pnl': max_dd,
            'max_drawdown_pct': (max_dd / trades_df.loc[dd_start_idx, 'cumulative_pnl'] * 100) if trades_df.loc[dd_start_idx, 'cumulative_pnl'] != 0 else 0,
            'drawdown_duration_days': dd_duration_days,
            'drawdown_start_date': dd_start_time.date().isoformat(),
            'drawdown_end_date': dd_end_time.date().isoformat(),
            'recovered': recovered,
            'recovery_time_days': recovery_time,
            'current_drawdown': trades_df['drawdown'].iloc[-1],
        }

    def analyze_risk_adjusted_returns(
        self,
        strategy: Optional[str] = None,
        days: int = 90
    ) -> Dict:
        """
        Calculate risk-adjusted performance metrics.

        Professional metrics:
        - Sharpe Ratio
        - Sortino Ratio
        - Calmar Ratio
        - MAR Ratio

        Args:
            strategy: Filter by strategy
            days: Number of days

        Returns:
            Risk-adjusted metrics
        """
        start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        trades_df = self.db.get_trades(strategy=strategy, start_date=start_date)

        if len(trades_df) == 0:
            return {'error': 'No trades found'}

        returns = trades_df['pnl_pct'] / 100  # Convert to decimal

        # Sharpe Ratio
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0

        # Sortino Ratio (only downside deviation)
        downside_returns = returns[returns < 0]
        sortino = (
            (returns.mean() / downside_returns.std()) * np.sqrt(252)
            if len(downside_returns) > 0 and downside_returns.std() > 0
            else 0
        )

        # Calculate drawdown for Calmar
        trades_df = trades_df.sort_values('entry_time')
        trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
        trades_df['running_max'] = trades_df['cumulative_pnl'].expanding().max()
        trades_df['drawdown'] = trades_df['cumulative_pnl'] - trades_df['running_max']

        max_dd = abs(trades_df['drawdown'].min())

        # Calmar Ratio
        annual_return = returns.mean() * 252 * 100  # Annualized
        calmar = annual_return / max_dd if max_dd > 0 else 0

        return {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'annual_return_pct': annual_return,
            'volatility_pct': returns.std() * np.sqrt(252) * 100,
            'downside_volatility_pct': downside_returns.std() * np.sqrt(252) * 100 if len(downside_returns) > 0 else 0,
        }

    # =========================================================================
    # REPORTING
    # =========================================================================

    def generate_report(
        self,
        strategy: Optional[str] = None,
        days: int = 30
    ) -> str:
        """
        Generate comprehensive analysis report.

        Args:
            strategy: Filter by strategy
            days: Number of days

        Returns:
            Formatted report string
        """
        report = []
        report.append("\n" + "="*80)
        report.append("COMPREHENSIVE TRADE ANALYSIS REPORT")
        report.append("="*80)
        report.append(f"\nPeriod: Last {days} days")
        if strategy:
            report.append(f"Strategy: {strategy}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 1. Win/Loss Patterns
        report.append("\n" + "-"*80)
        report.append("1. WIN/LOSS ANALYSIS")
        report.append("-"*80)

        wl_analysis = self.analyze_win_loss_patterns(strategy=strategy, days=days)
        if 'error' not in wl_analysis:
            report.append(f"Total Trades:       {wl_analysis['total_trades']}")
            report.append(f"Win Rate:           {wl_analysis['win_rate']:.2f}%")
            report.append(f"Profit Factor:      {wl_analysis['profit_factor']:.2f}")
            report.append(f"\nWinners:")
            report.append(f"  Average:          {wl_analysis['avg_win_pct']:.2f}%")
            report.append(f"  Best:             {wl_analysis['best_win']:.2f}%")
            report.append(f"  Avg Duration:     {wl_analysis['avg_win_duration']:.1f}h")
            report.append(f"\nLosers:")
            report.append(f"  Average:          {wl_analysis['avg_loss_pct']:.2f}%")
            report.append(f"  Worst:            {wl_analysis['worst_loss']:.2f}%")
            report.append(f"  Avg Duration:     {wl_analysis['avg_loss_duration']:.1f}h")
            report.append(f"\nRisk/Reward Ratio:  {wl_analysis['avg_rr_ratio']:.2f}")

        # 2. Risk-Adjusted Returns
        report.append("\n" + "-"*80)
        report.append("2. RISK-ADJUSTED PERFORMANCE")
        report.append("-"*80)

        risk_adj = self.analyze_risk_adjusted_returns(strategy=strategy, days=days)
        if 'error' not in risk_adj:
            report.append(f"Annual Return:      {risk_adj['annual_return_pct']:.2f}%")
            report.append(f"Sharpe Ratio:       {risk_adj['sharpe_ratio']:.2f}")
            report.append(f"Sortino Ratio:      {risk_adj['sortino_ratio']:.2f}")
            report.append(f"Calmar Ratio:       {risk_adj['calmar_ratio']:.2f}")
            report.append(f"Volatility:         {risk_adj['volatility_pct']:.2f}%")

        # 3. Drawdown Analysis
        report.append("\n" + "-"*80)
        report.append("3. DRAWDOWN ANALYSIS")
        report.append("-"*80)

        dd_analysis = self.analyze_drawdowns(strategy=strategy, days=days)
        if 'error' not in dd_analysis:
            report.append(f"Max Drawdown:       {dd_analysis['max_drawdown_pct']:.2f}%")
            report.append(f"DD Duration:        {dd_analysis['drawdown_duration_days']} days")
            report.append(f"Recovered:          {'Yes' if dd_analysis['recovered'] else 'No'}")
            if dd_analysis['recovery_time_days']:
                report.append(f"Recovery Time:      {dd_analysis['recovery_time_days']} days")

        # 4. Consecutive Trades
        report.append("\n" + "-"*80)
        report.append("4. STREAK ANALYSIS")
        report.append("-"*80)

        streak_analysis = self.analyze_consecutive_trades(strategy=strategy, days=days)
        if 'error' not in streak_analysis:
            report.append(f"Max Win Streak:     {streak_analysis['max_win_streak']:.0f}")
            report.append(f"Max Loss Streak:    {streak_analysis['max_loss_streak']:.0f}")
            report.append(f"\nPerformance After:")
            report.append(f"  After Win:        {streak_analysis['avg_trade_after_win']:.2f}%")
            report.append(f"  After Loss:       {streak_analysis['avg_trade_after_loss']:.2f}%")
            if streak_analysis['revenge_trading']:
                report.append(f"\n⚠ WARNING: Possible revenge trading detected!")
                report.append(f"  Performance drops after losses.")

        report.append("\n" + "="*80 + "\n")

        return "\n".join(report)
