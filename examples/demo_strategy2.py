"""
DEMO - Strategy 2 (Volatility Breakout)
=======================================

This strategy generates MORE trades than Strategy 1!
Perfect for testing the journaling system.
"""

import sys
sys.path.append('..')

from config.config import Config, VolatilityBreakoutConfig
from strategies import VolatilityNormalizationBreakout
from backtest import Backtester, DataLoader
from risk import RiskManager, PositionSizer
from journal import JournalManager, TradeAnalyzer, Reporter


def run_strategy2_demo():
    """Run Strategy 2 - generates more trades!"""

    print("\n" + "="*80)
    print("STRATEGY 2 DEMO - VOLATILITY BREAKOUT")
    print("="*80 + "\n")
    print("📈 This strategy looks for breakouts from consolidation")
    print("   Generates MORE trades than Strategy 1!\n")

    # Initialize Journal
    print("Initializing trade journal...")
    journal = JournalManager(db_path="data/trading_journal.db")
    print("✓ Journal ready")

    # Configure Strategy 2
    print("\nConfiguring Volatility Breakout strategy...")
    config = VolatilityBreakoutConfig(
        assets=["BTC/USDT:USDT"],
        timeframe="1h",
    )

    # Slightly relax for demo
    config.params.bandwidth_percentile = 30  # 30th percentile instead of 20th
    config.params.volume_threshold = 1.0  # Accept normal volume

    full_config = Config(strategies=[config])
    full_config.backtest.initial_capital = 100_000

    print("✓ Strategy 2 configured")

    # Load data with periods of consolidation and breakouts
    print("\nLoading market data...")
    data_loader = DataLoader()

    btc_data = data_loader.generate_synthetic_data(
        symbol="BTC/USDT",
        start_date="2023-01-01",
        end_date="2023-03-01",  # 2 months for more signals
        timeframe="1h",
        initial_price=42000.0,
        volatility=0.03  # Moderate volatility
    )

    market_data = {"BTC/USDT:USDT": btc_data}
    print(f"✓ Loaded {len(btc_data)} candles")

    # Initialize
    print("\nInitializing components...")
    position_sizer = PositionSizer(portfolio_value=full_config.backtest.initial_capital)
    risk_manager = RiskManager(full_config.risk)
    risk_manager.initialize(full_config.backtest.initial_capital)

    strategy = VolatilityNormalizationBreakout(
        config=config,
        risk_manager=risk_manager,
        position_sizer=position_sizer
    )
    print("✓ Ready")

    # Run
    print("\nRunning backtest...")
    print("-" * 80)

    backtester = Backtester(full_config, journal_manager=journal)
    metrics = backtester.run(strategy, market_data)

    # Results
    print("\n" + "="*80)
    print("RESULTS - STRATEGY 2")
    print("="*80 + "\n")

    if metrics.total_trades == 0:
        print("⚠ No trades. Synthetic data might not have clear breakout patterns.")
        print("   This can happen with random data.")
    else:
        print(f"✓ Generated {metrics.total_trades} trades!")
        print(metrics)

        # Analysis
        print("\n" + "="*80)
        print("ANALYSIS")
        print("="*80 + "\n")

        journal.print_summary(days=60)

        analyzer = TradeAnalyzer(journal.db)
        wl = analyzer.analyze_win_loss_patterns(days=60)

        if 'error' not in wl:
            print(f"\nWin Rate:          {wl['win_rate']:.2f}%")
            print(f"Profit Factor:     {wl['profit_factor']:.2f}")
            print(f"Avg Win:           {wl['avg_win_pct']:.2f}%")
            print(f"Avg Loss:          {wl['avg_loss_pct']:.2f}%")

    print("\n" + "="*80)
    print("✓ All trades logged to database!")
    print("="*80 + "\n")

    journal.close()
    return metrics


if __name__ == "__main__":
    run_strategy2_demo()
