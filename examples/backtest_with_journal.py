"""
BACKTEST WITH TRADE JOURNALING - EXAMPLE
========================================

This example shows you how to:
1. Run a backtest with automatic journaling
2. Analyze the results
3. Generate reports
4. Export data

All your trades are permanently logged to a database!
"""

import sys
sys.path.append('..')

from config.config import Config, LiquidityImbalanceConfig
from strategies import LiquidityImbalanceMeanReversion
from backtest import Backtester, DataLoader
from risk import RiskManager, PositionSizer
from journal import JournalManager, TradeAnalyzer, Reporter


def run_backtest_with_journal():
    """Run a backtest and log everything to journal."""

    print("\n" + "="*80)
    print("BACKTEST WITH AUTOMATIC TRADE JOURNALING")
    print("="*80 + "\n")

    # Step 1: Initialize Journal
    print("Step 1: Initializing trade journal...")
    journal = JournalManager(db_path="data/trading_journal.db")
    print("✓ Journal initialized")

    # Step 2: Configure Strategy
    print("\nStep 2: Configuring strategy...")
    config = LiquidityImbalanceConfig(
        assets=["BTC/USDT:USDT"],
        timeframe="5m",
    )

    full_config = Config(strategies=[config])
    full_config.backtest.initial_capital = 100_000

    print("✓ Strategy configured")

    # Step 3: Load Market Data
    print("\nStep 3: Loading market data...")
    data_loader = DataLoader()

    btc_data = data_loader.generate_synthetic_data(
        symbol="BTC/USDT",
        start_date="2023-01-01",
        end_date="2023-06-30",  # 6 months
        timeframe="5m",
        initial_price=42000.0,
        volatility=0.02
    )

    market_data = {"BTC/USDT:USDT": btc_data}
    print(f"✓ Loaded {len(btc_data)} candles")

    # Step 4: Initialize Components
    print("\nStep 4: Initializing trading components...")
    position_sizer = PositionSizer(
        portfolio_value=full_config.backtest.initial_capital
    )

    risk_manager = RiskManager(full_config.risk)
    risk_manager.initialize(full_config.backtest.initial_capital)

    strategy = LiquidityImbalanceMeanReversion(
        config=config,
        risk_manager=risk_manager,
        position_sizer=position_sizer
    )

    print("✓ Components ready")

    # Step 5: Run Backtest with Journaling
    print("\nStep 5: Running backtest with automatic journaling...")
    print("-" * 80)

    backtester = Backtester(full_config, journal_manager=journal)
    metrics = backtester.run(strategy, market_data)

    # Step 6: Display Results
    print("\n" + "="*80)
    print("BACKTEST COMPLETE - RESULTS LOGGED TO JOURNAL")
    print("="*80 + "\n")

    print(metrics)

    # Step 7: Analyze Results
    print("\n" + "="*80)
    print("ANALYZING LOGGED TRADES")
    print("="*80 + "\n")

    analyzer = TradeAnalyzer(journal.db)

    # 7.1 Quick Summary
    print("Quick Summary (Last 30 Days):")
    print("-" * 80)
    journal.print_summary(days=180)  # 6 months

    # 7.2 Win/Loss Analysis
    print("\nWin/Loss Patterns:")
    print("-" * 80)
    wl_analysis = analyzer.analyze_win_loss_patterns(days=180)
    if 'error' not in wl_analysis:
        print(f"Win Rate:          {wl_analysis['win_rate']:.2f}%")
        print(f"Profit Factor:     {wl_analysis['profit_factor']:.2f}")
        print(f"Avg Win:           {wl_analysis['avg_win_pct']:.2f}%")
        print(f"Avg Loss:          {wl_analysis['avg_loss_pct']:.2f}%")
        print(f"Risk/Reward:       {wl_analysis['avg_rr_ratio']:.2f}")

    # 7.3 Time Analysis
    print("\n\nBest Trading Hours:")
    print("-" * 80)
    hourly = analyzer.analyze_time_of_day(days=180)
    if len(hourly) > 0:
        print(hourly.head(5))

    # 7.4 Risk-Adjusted Metrics
    print("\n\nRisk-Adjusted Performance:")
    print("-" * 80)
    risk_adj = analyzer.analyze_risk_adjusted_returns(days=180)
    if 'error' not in risk_adj:
        print(f"Sharpe Ratio:      {risk_adj['sharpe_ratio']:.2f}")
        print(f"Sortino Ratio:     {risk_adj['sortino_ratio']:.2f}")
        print(f"Annual Return:     {risk_adj['annual_return_pct']:.2f}%")

    # Step 8: Generate Reports
    print("\n\n" + "="*80)
    print("GENERATING REPORTS")
    print("="*80)

    reporter = Reporter(journal.db)

    # Generate comprehensive report
    report = analyzer.generate_report(days=180)
    print(report)

    # Save report to file
    reporter.export_report_to_file(
        report,
        filename="backtest_analysis.txt",
        output_dir="reports"
    )

    # Step 9: Export Data
    print("\n" + "="*80)
    print("EXPORTING DATA")
    print("="*80 + "\n")

    journal.export_all(output_dir="exports")

    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80 + "\n")

    print("Your data is now permanently logged!")
    print("\nYou can:")
    print("  1. View trades: journal.db.get_trades()")
    print("  2. Analyze: analyzer.analyze_win_loss_patterns()")
    print("  3. Report: reporter.daily_summary()")
    print("  4. Export: journal.export_all()")
    print("\nDatabase location: data/trading_journal.db")

    journal.close()

    return metrics


def analyze_existing_journal():
    """Analyze trades already in the journal."""

    print("\n" + "="*80)
    print("ANALYZING EXISTING JOURNAL")
    print("="*80 + "\n")

    # Open journal
    journal = JournalManager()
    analyzer = TradeAnalyzer(journal.db)
    reporter = Reporter(journal.db)

    # Get all trades
    trades_df = journal.db.get_trades()

    if len(trades_df) == 0:
        print("No trades in journal yet. Run a backtest first!")
        return

    print(f"Found {len(trades_df)} trades in journal\n")

    # Full analysis
    print("Generating comprehensive analysis...")
    report = analyzer.generate_report(days=365)
    print(report)

    # Monthly report
    print("\nGenerating monthly report...")
    monthly = reporter.monthly_report()
    print(monthly)

    journal.close()


def main():
    """Main function."""

    import argparse

    parser = argparse.ArgumentParser(
        description="Run backtest with trade journaling"
    )

    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze existing journal instead of running backtest'
    )

    args = parser.parse_args()

    if args.analyze:
        analyze_existing_journal()
    else:
        run_backtest_with_journal()


if __name__ == "__main__":
    main()
