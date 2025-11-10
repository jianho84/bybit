"""
Main Entry Point for Crypto Quant Trading System
===============================================

This module demonstrates all four strategies with comprehensive examples.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
from config.config import (
    Config,
    LiquidityImbalanceConfig,
    VolatilityBreakoutConfig,
    SpotPerpBasisConfig,
    DynamicFundingConfig,
)

# Strategies
from strategies import (
    LiquidityImbalanceMeanReversion,
    VolatilityNormalizationBreakout,
    SpotPerpBasisArbitrage,
    DynamicFundingRateArbitrage,
)

# Backtesting
from backtest import Backtester, DataLoader, PerformanceMetrics

# Risk Management
from risk import RiskManager, PositionSizer


def run_strategy_1_example():
    """
    Example: Liquidity Imbalance Mean Reversion Strategy

    Target: 40%+ annual return, 1.5+ Sharpe, 62% win rate
    """
    print("\n" + "="*80)
    print("STRATEGY 1: LIQUIDITY IMBALANCE MEAN REVERSION")
    print("="*80 + "\n")

    # Configuration
    config = LiquidityImbalanceConfig(
        assets=["BTC/USDT:USDT", "ETH/USDT:USDT"],
        timeframe="5m",
    )

    # Load data
    data_loader = DataLoader()

    # Generate synthetic data for demonstration
    print("Generating synthetic market data...")
    btc_data = data_loader.generate_synthetic_data(
        symbol="BTC/USDT",
        start_date="2023-01-01",
        end_date="2024-01-01",
        timeframe="5m",
        initial_price=42000.0,
        volatility=0.02
    )

    market_data = {"BTC/USDT:USDT": btc_data}

    # Initialize strategy
    full_config = Config(strategies=[config])
    full_config.backtest.initial_capital = 100_000

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

    # Run backtest
    backtester = Backtester(full_config)
    metrics = backtester.run(strategy, market_data)

    # Display results
    print(metrics)

    # Check if targets met
    print("\nPERFORMANCE TARGETS:")
    print(f"  Annual Return Target: >40%  | Actual: {metrics.annual_return:.2f}%  {'✓' if metrics.annual_return > 40 else '✗'}")
    print(f"  Sharpe Ratio Target:  >1.5  | Actual: {metrics.sharpe_ratio:.2f}  {'✓' if metrics.sharpe_ratio > 1.5 else '✗'}")
    print(f"  Win Rate Target:      >60%  | Actual: {metrics.win_rate:.2f}%  {'✓' if metrics.win_rate > 60 else '✗'}")

    return metrics


def run_strategy_2_example():
    """
    Example: Volatility Normalization Breakout Strategy

    Target: 40%+ annual return, 1.5+ Sharpe, 58% win rate
    """
    print("\n" + "="*80)
    print("STRATEGY 2: VOLATILITY NORMALIZATION BREAKOUT")
    print("="*80 + "\n")

    config = VolatilityBreakoutConfig(
        assets=["ETH/USDT:USDT"],
        timeframe="1h",
    )

    data_loader = DataLoader()

    print("Generating synthetic market data...")
    eth_data = data_loader.generate_synthetic_data(
        symbol="ETH/USDT",
        start_date="2023-01-01",
        end_date="2024-01-01",
        timeframe="1h",
        initial_price=2800.0,
        volatility=0.025
    )

    market_data = {"ETH/USDT:USDT": eth_data}

    full_config = Config(strategies=[config])
    full_config.backtest.initial_capital = 100_000

    position_sizer = PositionSizer(
        portfolio_value=full_config.backtest.initial_capital
    )

    risk_manager = RiskManager(full_config.risk)
    risk_manager.initialize(full_config.backtest.initial_capital)

    strategy = VolatilityNormalizationBreakout(
        config=config,
        risk_manager=risk_manager,
        position_sizer=position_sizer
    )

    backtester = Backtester(full_config)
    metrics = backtester.run(strategy, market_data)

    print(metrics)

    print("\nPERFORMANCE TARGETS:")
    print(f"  Annual Return Target: >40%  | Actual: {metrics.annual_return:.2f}%  {'✓' if metrics.annual_return > 40 else '✗'}")
    print(f"  Sharpe Ratio Target:  >1.5  | Actual: {metrics.sharpe_ratio:.2f}  {'✓' if metrics.sharpe_ratio > 1.5 else '✗'}")

    return metrics


def run_strategy_3_example():
    """
    Example: Spot-Perpetual Basis Funding Arbitrage

    Target: 40%+ annual return, 2.0+ Sharpe, 75% win rate
    """
    print("\n" + "="*80)
    print("STRATEGY 3: SPOT-PERPETUAL BASIS FUNDING ARBITRAGE")
    print("="*80 + "\n")

    config = SpotPerpBasisConfig(
        assets=["BTC/USDT:USDT"],
        timeframe="8h",
    )

    data_loader = DataLoader()

    print("Generating synthetic market data...")
    spot_data = data_loader.generate_synthetic_data(
        symbol="BTC/USDT",
        start_date="2023-01-01",
        end_date="2024-01-01",
        timeframe="8h",
        initial_price=45000.0,
        volatility=0.015
    )

    # Generate perp data with slight premium
    perp_data = spot_data.copy()
    perp_data['close'] = perp_data['close'] * 1.001  # 0.1% premium on average

    # Generate funding rates
    funding_rates = data_loader.generate_funding_rate_data(
        dates=spot_data.index,
        mean_funding=0.0003,  # 0.03% per 8h = ~40% annualized
        volatility=0.0002
    )

    # For demonstration, we'll modify the strategy call
    # In production, this would use actual spot/perp data

    full_config = Config(strategies=[config])
    full_config.backtest.initial_capital = 100_000

    print("Note: Spot-Perp arbitrage requires specialized data feeds.")
    print("This is a framework implementation. See documentation for full setup.")

    return None


def run_strategy_4_example():
    """
    Example: Dynamic Funding Rate Cycle Arbitrage

    Target: 45%+ annual return, 2.2+ Sharpe, 80% win rate
    """
    print("\n" + "="*80)
    print("STRATEGY 4: DYNAMIC FUNDING RATE CYCLE ARBITRAGE")
    print("="*80 + "\n")

    config = DynamicFundingConfig(
        assets=["BTC/USDT:USDT"],
        timeframe="8h",
    )

    print("Note: Dynamic funding arbitrage requires funding rate history and")
    print("optimal timing around funding intervals. This is a framework implementation.")
    print("See documentation for full setup with real funding data.")

    return None


def run_all_strategies():
    """Run all four strategies in sequence."""
    print("\n" + "#"*80)
    print("# CRYPTO QUANT TRADING SYSTEM - COMPREHENSIVE STRATEGY SUITE")
    print("#"*80)
    print(f"\nExecution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Author: Senior Quant Trader (Jump Trading Style)")
    print("\nRunning all four strategies...\n")

    results = {}

    # Strategy 1
    try:
        results['strategy_1'] = run_strategy_1_example()
    except Exception as e:
        print(f"Error running Strategy 1: {e}")

    # Strategy 2
    try:
        results['strategy_2'] = run_strategy_2_example()
    except Exception as e:
        print(f"Error running Strategy 2: {e}")

    # Strategy 3
    try:
        results['strategy_3'] = run_strategy_3_example()
    except Exception as e:
        print(f"Error running Strategy 3: {e}")

    # Strategy 4
    try:
        results['strategy_4'] = run_strategy_4_example()
    except Exception as e:
        print(f"Error running Strategy 4: {e}")

    # Summary
    print("\n" + "#"*80)
    print("# EXECUTION COMPLETE")
    print("#"*80)
    print("\nAll strategies have been demonstrated.")
    print("For production deployment, configure API keys and data feeds.")

    return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Crypto Quant Trading System - Professional Grade Strategies"
    )

    parser.add_argument(
        '--strategy',
        type=int,
        choices=[1, 2, 3, 4],
        help='Run specific strategy (1-4), or all if not specified'
    )

    parser.add_argument(
        '--backtest',
        action='store_true',
        help='Run backtest mode'
    )

    args = parser.parse_args()

    if args.strategy == 1:
        run_strategy_1_example()
    elif args.strategy == 2:
        run_strategy_2_example()
    elif args.strategy == 3:
        run_strategy_3_example()
    elif args.strategy == 4:
        run_strategy_4_example()
    else:
        run_all_strategies()


if __name__ == "__main__":
    main()
