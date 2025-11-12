"""
QUICK TEST - Backtest with Journaling (Fast Version)
====================================================

This is optimized for FAST testing:
- 1 month of data only
- 1-hour timeframe
- Runs in ~30 seconds instead of 50+ minutes!
"""

import sys
sys.path.append('..')

from config.config import Config, LiquidityImbalanceConfig
from strategies import LiquidityImbalanceMeanReversion
from backtest import Backtester, DataLoader
from risk import RiskManager, PositionSizer
from journal import JournalManager, TradeAnalyzer, Reporter


def run_quick_test():
    """Run a FAST backtest for testing."""

    print("\n" + "="*80)
    print("QUICK TEST - BACKTEST WITH JOURNALING")
    print("="*80 + "\n")
    print("⚡ This version is optimized for speed!")
    print("   - 1 month of data (vs 6 months)")
    print("   - 1-hour timeframe (vs 5-minute)")
    print("   - Should complete in ~30 seconds\n")

    # Step 1: Initialize Journal
    print("Step 1: Initializing trade journal...")
    journal = JournalManager(db_path="data/trading_journal.db")
    print("✓ Journal initialized")

    # Step 2: Configure Strategy
    print("\nStep 2: Configuring strategy...")
    config = LiquidityImbalanceConfig(
        assets=["BTC/USDT:USDT"],
        timeframe="1h",  # Faster than 5m
    )

    full_config = Config(strategies=[config])
    full_config.backtest.initial_capital = 100_000

    print("✓ Strategy configured")

    # Step 3: Load Market Data (LESS DATA = FASTER)
    print("\nStep 3: Loading market data...")
    data_loader = DataLoader()

    btc_data = data_loader.generate_synthetic_data(
        symbol="BTC/USDT",
        start_date="2023-01-01",
        end_date="2023-02-01",  # Only 1 month!
        timeframe="1h",  # 1-hour candles
        initial_price=42000.0,
        volatility=0.02
    )

    market_data = {"BTC/USDT:USDT": btc_data}
    print(f"✓ Loaded {len(btc_data)} candles (much faster!)")

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

    # Step 5: Run Backtest
    print("\nStep 5: Running backtest...")
    print("-" * 80)

    backtester = Backtester(full_config, journal_manager=journal)
    metrics = backtester.run(strategy, market_data)

    # Step 6: Display Results
    print("\n" + "="*80)
    print("BACKTEST COMPLETE - RESULTS")
    print("="*80 + "\n")

    print(metrics)

    # Step 7: Quick Analysis
    print("\n" + "="*80)
    print("QUICK ANALYSIS")
    print("="*80 + "\n")

    journal.print_summary(days=30)

    # Step 8: Analyze
    analyzer = TradeAnalyzer(journal.db)

    print("\nWin/Loss Patterns:")
    print("-" * 80)
    wl_analysis = analyzer.analyze_win_loss_patterns(days=30)
    if 'error' not in wl_analysis:
        print(f"Win Rate:          {wl_analysis['win_rate']:.2f}%")
        print(f"Profit Factor:     {wl_analysis['profit_factor']:.2f}")
        print(f"Avg Win:           {wl_analysis['avg_win_pct']:.2f}%")
        print(f"Avg Loss:          {wl_analysis['avg_loss_pct']:.2f}%")

    print("\n" + "="*80)
    print("DONE!")
    print("="*80 + "\n")

    print("✓ All data logged to: data/trading_journal.db")
    print("\nNext steps:")
    print("  1. Analyze more: python backtest_with_journal.py --analyze")
    print("  2. Run tutorial: python analyze_trades.py")
    print("  3. For full 6-month test, edit the dates in this file")

    journal.close()
    return metrics


if __name__ == "__main__":
    run_quick_test()
