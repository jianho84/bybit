"""
HOW TO ANALYZE YOUR TRADES - COMPLETE TUTORIAL
==============================================

This tutorial teaches you how to analyze your trading performance
like a professional quantitative trader.

You'll learn:
1. How to query your trade journal
2. Common analyses every trader should do
3. How to identify and fix problems
4. Advanced performance metrics
5. Automated reporting

Let's get started!
"""

import sys
sys.path.append('..')

from journal import JournalManager, TradeAnalyzer, Reporter
import pandas as pd


def tutorial_1_basic_queries():
    """Tutorial 1: Basic Database Queries"""

    print("\n" + "="*80)
    print("TUTORIAL 1: BASIC QUERIES")
    print("="*80 + "\n")

    # Initialize journal
    journal = JournalManager()

    print("1.1 Get All Trades")
    print("-" * 80)
    print("""
    To get all your trades:

        trades_df = journal.db.get_trades()

    This returns a pandas DataFrame with all trades.
    """)

    trades_df = journal.db.get_trades()
    print(f"Total trades in database: {len(trades_df)}")

    if len(trades_df) > 0:
        print("\nFirst 5 trades:")
        print(trades_df.head())

    print("\n\n1.2 Filter by Strategy")
    print("-" * 80)
    print("""
    To filter by strategy:

        strategy1_trades = journal.db.get_trades(strategy='LiquidityImbalanceMeanReversion')

    Useful for comparing strategy performance.
    """)

    print("\n\n1.3 Filter by Date Range")
    print("-" * 80)
    print("""
    To get trades from a specific period:

        recent_trades = journal.db.get_trades(
            start_date='2024-01-01',
            end_date='2024-01-31'
        )

    Perfect for monthly reviews.
    """)

    print("\n\n1.4 Filter by Asset")
    print("-" * 80)
    print("""
    To analyze specific coins:

        btc_trades = journal.db.get_trades(asset='BTC/USDT:USDT')

    See which assets work best for your strategy.
    """)

    input("\nPress Enter to continue to Tutorial 2...")


def tutorial_2_win_loss_analysis():
    """Tutorial 2: Win/Loss Analysis"""

    print("\n" + "="*80)
    print("TUTORIAL 2: WIN/LOSS ANALYSIS")
    print("="*80 + "\n")

    journal = JournalManager()
    analyzer = TradeAnalyzer(journal.db)

    print("""
    Win/Loss analysis helps you understand:
    - Are your winners big enough?
    - Are your losers too big?
    - Are you cutting winners too early?
    - Are you holding losers too long?

    Let's analyze...
    """)

    # Get win/loss analysis
    analysis = analyzer.analyze_win_loss_patterns(days=30)

    if 'error' in analysis:
        print("No trades found. Run a backtest first!")
        return

    print("\nRESULTS:")
    print("-" * 80)
    print(f"Win Rate:           {analysis['win_rate']:.2f}%")
    print(f"Profit Factor:      {analysis['profit_factor']:.2f}")
    print(f"\nAverage Win:        {analysis['avg_win_pct']:.2f}%")
    print(f"Average Loss:       {analysis['avg_loss_pct']:.2f}%")
    print(f"Risk/Reward Ratio:  {analysis['avg_rr_ratio']:.2f}")

    print("\n\nINTERPRETATION:")
    print("-" * 80)

    if analysis['win_rate'] < 50:
        print("⚠ Win rate < 50%:")
        print("  - Need bigger average wins")
        print("  - Or smaller average losses")
        print("  - Check if you're exiting winners too early")

    if analysis['profit_factor'] < 1.5:
        print("⚠ Profit factor < 1.5:")
        print("  - Not enough edge")
        print("  - Review entry criteria")
        print("  - May need to be more selective")

    if analysis['avg_rr_ratio'] < 1.5:
        print("⚠ Risk/Reward < 1.5:")
        print("  - Winners aren't big enough vs losers")
        print("  - Consider wider profit targets")
        print("  - Or tighter stop losses")

    print("\n\nWHAT TO DO:")
    print("-" * 80)
    print("""
    1. If Win Rate is high (>60%) but Profit Factor is low:
       → You're cutting winners too early
       → Try wider targets or trailing stops

    2. If Win Rate is low (<45%) but winners are big:
       → This is OK if Profit Factor > 1.5
       → You're a "home run" trader

    3. If both Win Rate AND Profit Factor are low:
       → Strategy needs work
       → Review entry/exit rules
       → Filter for higher quality setups
    """)

    input("\nPress Enter to continue to Tutorial 3...")


def tutorial_3_time_analysis():
    """Tutorial 3: Time-Based Analysis"""

    print("\n" + "="*80)
    print("TUTORIAL 3: TIME-BASED ANALYSIS")
    print("="*80 + "\n")

    journal = JournalManager()
    analyzer = TradeAnalyzer(journal.db)

    print("""
    Time analysis reveals:
    - Which hours are most profitable
    - When to avoid trading
    - If you have a time-of-day edge
    """)

    # Time of day analysis
    hourly = analyzer.analyze_time_of_day(days=30)

    if len(hourly) == 0:
        print("No trades found.")
        return

    print("\nPERFORMANCE BY HOUR (Top 5):")
    print("-" * 80)
    print(hourly.head())

    print("\n\nHOW TO USE THIS:")
    print("-" * 80)
    print("""
    1. Find your best hours:
       - Trade more during profitable hours
       - Increase position size during edge hours

    2. Identify bad hours:
       - Avoid trading during losing hours
       - May be low liquidity or bad spreads

    3. Look for patterns:
       - Asia vs US vs Europe sessions
       - Open/close times
       - News release times

    EXAMPLE:
    If hours 14-16 UTC are always profitable:
    → Focus trading in that window
    → May align with US market open
    → Higher volume = better execution
    """)

    input("\nPress Enter to continue to Tutorial 4...")


def tutorial_4_asset_analysis():
    """Tutorial 4: Asset Performance"""

    print("\n" + "="*80)
    print("TUTORIAL 4: ASSET ANALYSIS")
    print("="*80 + "\n")

    journal = JournalManager()
    analyzer = TradeAnalyzer(journal.db)

    print("""
    Asset analysis shows:
    - Which coins your strategy works best on
    - Which to avoid
    - If you should specialize
    """)

    by_asset = analyzer.analyze_by_asset(days=30)

    if len(by_asset) == 0:
        print("No trades found.")
        return

    print("\nPERFORMANCE BY ASSET:")
    print("-" * 80)
    print(by_asset)

    print("\n\nINTERPRETATION:")
    print("-" * 80)
    print("""
    Look for:

    1. Clear Winners:
       - High win rate + high profit factor
       - Trade these more

    2. Clear Losers:
       - Low win rate + low profit factor
       - Stop trading these!

    3. High Volume Coins:
       - BTC/ETH usually have best liquidity
       - Tighter spreads = better execution

    4. Volatility Differences:
       - Low volatility coins: need tighter stops
       - High volatility: wider stops, smaller position size

    SPECIALIZATION:
    If one coin dominates your performance:
    → Consider specializing
    → You may have found your edge
    → Master that one instrument
    """)

    input("\nPress Enter to continue to Tutorial 5...")


def tutorial_5_strategy_comparison():
    """Tutorial 5: Strategy Comparison"""

    print("\n" + "="*80)
    print("TUTORIAL 5: STRATEGY COMPARISON")
    print("="*80 + "\n")

    journal = JournalManager()
    analyzer = TradeAnalyzer(journal.db)

    print("""
    Compare your strategies to find:
    - Which performs best
    - Which needs improvement
    - How to allocate capital
    """)

    by_strategy = analyzer.analyze_by_strategy(days=90)

    if len(by_strategy) == 0:
        print("No trades found.")
        return

    print("\nSTRATEGY COMPARISON:")
    print("-" * 80)
    print(by_strategy)

    print("\n\nKEY METRICS:")
    print("-" * 80)
    print("""
    Sharpe Ratio:
    - Measures risk-adjusted returns
    - > 2.0 is excellent
    - > 1.5 is good
    - < 1.0 needs work

    Profit Factor:
    - Total wins / Total losses
    - > 2.0 is excellent
    - > 1.5 is good
    - < 1.2 is marginal

    Win Rate:
    - % of winning trades
    - Needs to match strategy type
    - Mean reversion: 60-70%
    - Trend following: 40-50%

    CAPITAL ALLOCATION:
    Allocate more capital to:
    1. Highest Sharpe ratio (best risk-adjusted)
    2. Highest profit factor (most efficient)
    3. Lowest correlation (diversification)
    """)

    input("\nPress Enter to continue to Tutorial 6...")


def tutorial_6_advanced_analysis():
    """Tutorial 6: Advanced Analysis"""

    print("\n" + "="*80)
    print("TUTORIAL 6: ADVANCED ANALYSIS")
    print("="*80 + "\n")

    journal = JournalManager()
    analyzer = TradeAnalyzer(journal.db)

    print("6.1 Streak Analysis")
    print("-" * 80)
    print("""
    Analyzes consecutive wins/losses.
    Reveals psychological patterns:
    - Revenge trading after losses
    - Overconfidence after wins
    - When to take breaks
    """)

    streak_analysis = analyzer.analyze_consecutive_trades(days=90)

    if 'error' not in streak_analysis:
        print(f"\nMax Win Streak:     {streak_analysis['max_win_streak']}")
        print(f"Max Loss Streak:    {streak_analysis['max_loss_streak']}")
        print(f"\nAfter a Win:        {streak_analysis['avg_trade_after_win']:.2f}%")
        print(f"After a Loss:       {streak_analysis['avg_trade_after_loss']:.2f}%")

        if streak_analysis['revenge_trading']:
            print("\n⚠ REVENGE TRADING DETECTED!")
            print("You perform worse after losses.")
            print("→ Take a break after 2-3 losses in a row")
            print("→ Don't increase size to \"make it back\"")

    print("\n\n6.2 Drawdown Analysis")
    print("-" * 80)
    print("""
    Analyzes losing periods:
    - How bad it got
    - How long it lasted
    - Recovery time
    """)

    dd_analysis = analyzer.analyze_drawdowns(days=90)

    if 'error' not in dd_analysis:
        print(f"\nMax Drawdown:       {dd_analysis['max_drawdown_pct']:.2f}%")
        print(f"DD Duration:        {dd_analysis['drawdown_duration_days']} days")

        if dd_analysis['recovered']:
            print(f"Recovery Time:      {dd_analysis['recovery_time_days']} days")
        else:
            print("Status:             Still in drawdown")

        print(f"Current DD:         {dd_analysis['current_drawdown']:.2f}%")

    print("\n\n6.3 Risk-Adjusted Returns")
    print("-" * 80)
    print("""
    Professional metrics used by hedge funds:
    """)

    risk_adj = analyzer.analyze_risk_adjusted_returns(days=90)

    if 'error' not in risk_adj:
        print(f"\nSharpe Ratio:       {risk_adj['sharpe_ratio']:.2f}")
        print(f"Sortino Ratio:      {risk_adj['sortino_ratio']:.2f}")
        print(f"Calmar Ratio:       {risk_adj['calmar_ratio']:.2f}")
        print(f"\nAnnual Return:      {risk_adj['annual_return_pct']:.2f}%")
        print(f"Volatility:         {risk_adj['volatility_pct']:.2f}%")

        print("\n\nWHAT THESE MEAN:")
        print("""
        Sharpe Ratio:
        - Return per unit of risk
        - Higher is better
        - Target: > 1.5 for crypto

        Sortino Ratio:
        - Like Sharpe but only counts downside volatility
        - More realistic for asymmetric strategies
        - Should be higher than Sharpe

        Calmar Ratio:
        - Annual return / Max drawdown
        - Shows return relative to worst case
        - Target: > 2.0
        """)

    input("\nPress Enter to continue to Tutorial 7...")


def tutorial_7_reporting():
    """Tutorial 7: Automated Reporting"""

    print("\n" + "="*80)
    print("TUTORIAL 7: AUTOMATED REPORTING")
    print("="*80 + "\n")

    journal = JournalManager()
    reporter = Reporter(journal.db)

    print("""
    Generate professional reports automatically.
    """)

    print("\n7.1 Daily Summary")
    print("-" * 80)
    print("""
    Get today's performance:

        reporter = Reporter(journal.db)
        daily = reporter.daily_summary()
        print(daily)

    Run this every evening to review the day.
    """)

    print("\n\n7.2 Weekly Review")
    print("-" * 80)
    print("""
    Get this week's performance:

        weekly = reporter.weekly_review()
        print(weekly)

    Run every Sunday night.
    Identifies weekly patterns.
    """)

    print("\n\n7.3 Monthly Report")
    print("-" * 80)
    print("""
    Get monthly analysis:

        monthly = reporter.monthly_report()
        print(monthly)

    Comprehensive monthly review.
    Track long-term progress.
    """)

    print("\n\n7.4 Comprehensive Analysis")
    print("-" * 80)
    print("""
    Full analysis report:

        analyzer = TradeAnalyzer(journal.db)
        report = analyzer.generate_report(days=30)
        print(report)

    This includes everything:
    - Win/loss analysis
    - Risk metrics
    - Drawdowns
    - Streaks
    - Recommendations
    """)

    # Generate example report
    report = TradeAnalyzer(journal.db).generate_report(days=30)
    print(report)

    input("\nPress Enter to see export options...")


def tutorial_8_exporting():
    """Tutorial 8: Exporting Data"""

    print("\n" + "="*80)
    print("TUTORIAL 8: EXPORTING DATA")
    print("="*80 + "\n")

    journal = JournalManager()

    print("""
    Export your data for:
    - Excel analysis
    - Custom reports
    - Backup
    - Sharing with team
    """)

    print("\n8.1 Export to CSV")
    print("-" * 80)
    print("""
    Export all tables:

        journal.export_all(output_dir='exports')

    Creates CSV files:
    - signals_{timestamp}.csv
    - trades_{timestamp}.csv
    - daily_performance_{timestamp}.csv

    Open in Excel for custom analysis.
    """)

    print("\n\n8.2 Export Specific Table")
    print("-" * 80)
    print("""
    Export just trades:

        journal.db.export_to_csv(
            table='trades',
            output_path='my_trades.csv'
        )

    Tables available:
    - signals
    - trades
    - daily_performance
    """)

    print("\n\n8.3 Direct Pandas Analysis")
    print("-" * 80)
    print("""
    Get data as DataFrame for custom analysis:

        trades_df = journal.db.get_trades()

        # Your custom analysis
        trades_df['hour'] = trades_df['entry_time'].dt.hour
        hourly_pnl = trades_df.groupby('hour')['pnl'].sum()

    Full power of pandas at your fingertips!
    """)


def main():
    """Run complete tutorial."""

    print("\n" + "="*80)
    print("WELCOME TO THE TRADE ANALYSIS TUTORIAL")
    print("="*80)
    print("""
    This interactive tutorial will teach you how to analyze
    your trading performance like a professional quant trader.

    We'll cover:
    1. Basic database queries
    2. Win/loss analysis
    3. Time-based analysis
    4. Asset performance
    5. Strategy comparison
    6. Advanced analytics
    7. Automated reporting
    8. Data export

    Each section builds on the previous one.
    Take notes and try the examples yourself!
    """)

    input("\nPress Enter to start...")

    # Run tutorials
    tutorial_1_basic_queries()
    tutorial_2_win_loss_analysis()
    tutorial_3_time_analysis()
    tutorial_4_asset_analysis()
    tutorial_5_strategy_comparison()
    tutorial_6_advanced_analysis()
    tutorial_7_reporting()
    tutorial_8_exporting()

    print("\n" + "="*80)
    print("TUTORIAL COMPLETE!")
    print("="*80)
    print("""
    Congratulations! You now know how to analyze your trades
    like a professional quantitative trader.

    NEXT STEPS:
    1. Run a backtest with journaling enabled
    2. Use the analyses to identify issues
    3. Improve your strategy based on data
    4. Set up automated daily reports

    REMEMBER:
    - Data doesn't lie
    - Let analysis guide decisions
    - Track everything
    - Review regularly

    Happy trading!
    """)


if __name__ == "__main__":
    main()
