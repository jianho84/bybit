"""
DEMO MODE - Guaranteed To Generate Trades!
==========================================

This version uses:
- Relaxed strategy parameters (easier to trigger)
- Higher volatility synthetic data
- Guaranteed to generate trades for testing journaling system
"""

import sys
sys.path.append('..')

from config.config import Config, LiquidityImbalanceConfig
from strategies import LiquidityImbalanceMeanReversion
from backtest import Backtester, DataLoader
from risk import RiskManager, PositionSizer
from journal import JournalManager, TradeAnalyzer, Reporter


def run_demo():
    """Run demo with trades guaranteed."""

    print("\n" + "="*80)
    print("DEMO MODE - TRADES GUARANTEED!")
    print("="*80 + "\n")
    print("📊 This version uses relaxed parameters to generate trades")
    print("   Perfect for testing the journaling and analysis system!\n")

    # Initialize Journal
    print("Step 1: Initializing trade journal...")
    journal = JournalManager(db_path="data/trading_journal.db")
    print("✓ Journal initialized")

    # Configure Strategy with RELAXED parameters
    print("\nStep 2: Configuring strategy (DEMO MODE - relaxed parameters)...")
    config = LiquidityImbalanceConfig(
        assets=["BTC/USDT:USDT"],
        timeframe="1h",
    )

    # RELAX THE PARAMETERS FOR DEMO
    print("   • Lowering volume threshold: 4.2σ → 1.5σ (easier to trigger)")
    config.params.volume_sigma_threshold = 1.5  # Much easier to trigger

    print("   • Relaxing RSI thresholds: 30/70 → 45/55 (less extreme)")
    config.params.rsi_oversold = 45  # Less extreme
    config.params.rsi_overbought = 55  # Less extreme

    print("   • Reducing spread requirement: 80% → 30%")
    config.params.spread_consumption_pct = 0.30  # Less strict

    full_config = Config(strategies=[config])
    full_config.backtest.initial_capital = 100_000

    print("✓ Strategy configured for DEMO (will generate trades!)")

    # Load VOLATILE Market Data
    print("\nStep 3: Loading VOLATILE market data (generates more signals)...")
    data_loader = DataLoader()

    btc_data = data_loader.generate_synthetic_data(
        symbol="BTC/USDT",
        start_date="2023-01-01",
        end_date="2023-02-01",
        timeframe="1h",
        initial_price=42000.0,
        volatility=0.04  # 4% daily vol = more volatile = more trades!
    )

    market_data = {"BTC/USDT:USDT": btc_data}
    print(f"✓ Loaded {len(btc_data)} volatile candles")

    # Initialize Components
    print("\nStep 4: Initializing components...")
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

    # Run Backtest
    print("\nStep 5: Running backtest (should generate trades now!)...")
    print("-" * 80)

    backtester = Backtester(full_config, journal_manager=journal)
    metrics = backtester.run(strategy, market_data)

    # Display Results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80 + "\n")

    if metrics.total_trades == 0:
        print("⚠ Still no trades! The synthetic data might not have the right patterns.")
        print("   Try running this a few times - random data varies.")
        print("\n   Or try Strategy 2 (Volatility Breakout) which generates more trades:")
        print("   → python demo_strategy2.py")
    else:
        print(f"✓ SUCCESS! Generated {metrics.total_trades} trades")
        print(metrics)

        # Quick Analysis
        print("\n" + "="*80)
        print("TRADE ANALYSIS")
        print("="*80 + "\n")

        journal.print_summary(days=30)

        analyzer = TradeAnalyzer(journal.db)

        print("\nWin/Loss Analysis:")
        print("-" * 80)
        wl_analysis = analyzer.analyze_win_loss_patterns(days=30)
        if 'error' not in wl_analysis:
            print(f"Win Rate:          {wl_analysis['win_rate']:.2f}%")
            print(f"Profit Factor:     {wl_analysis['profit_factor']:.2f}")
            print(f"Avg Win:           {wl_analysis['avg_win_pct']:.2f}%")
            print(f"Avg Loss:          {wl_analysis['avg_loss_pct']:.2f}%")
            print(f"Best Trade:        {wl_analysis['best_win']:.2f}%")
            print(f"Worst Trade:       {wl_analysis['worst_loss']:.2f}%")

        # Show a few trade details
        trades_df = journal.db.get_trades()
        if len(trades_df) > 0:
            print(f"\nFirst 5 Trades:")
            print("-" * 80)
            print(trades_df[['asset', 'direction', 'entry_price', 'exit_price',
                            'pnl_pct', 'exit_reason']].head())

    print("\n" + "="*80)
    print("DONE!")
    print("="*80 + "\n")

    if metrics.total_trades > 0:
        print("✓ Trades logged to: data/trading_journal.db")
        print("\nNext steps:")
        print("  1. View all trades: journal.db.get_trades()")
        print("  2. Run analysis tutorial: python analyze_trades.py")
        print("  3. Try different strategies: python demo_strategy2.py")
    else:
        print("💡 Try Strategy 2 (Volatility Breakout) - generates more trades!")
        print("   It looks for breakouts instead of large orders, much more common.")

    journal.close()
    return metrics


if __name__ == "__main__":
    run_demo()
