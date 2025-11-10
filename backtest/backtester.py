"""
Backtester Module
=================
High-performance backtesting engine for crypto strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime

from backtest.metrics import calculate_metrics, PerformanceMetrics
from risk.risk_manager import RiskManager
from risk.position_sizer import PositionSizer
from strategies.base_strategy import BaseStrategy


class Backtester:
    """
    Vectorized backtesting engine.

    Features:
    - Realistic slippage and fees simulation
    - Position management
    - Risk controls
    - Performance analytics
    """

    def __init__(self, config):
        """
        Initialize backtester.

        Args:
            config: Backtest configuration
        """
        self.config = config

        # Initialize components
        self.risk_manager = RiskManager(config.risk if hasattr(config, 'risk') else None)
        self.position_sizer = PositionSizer(
            portfolio_value=config.backtest.initial_capital,
            max_position_size=config.risk.max_position_size if hasattr(config, 'risk') else 0.25
        )

        # State
        self.equity_curve = pd.Series(dtype=float)
        self.trades = []
        self.signals = []

    def run(
        self,
        strategy: BaseStrategy,
        market_data: Dict[str, pd.DataFrame],
        funding_data: Optional[Dict[str, pd.Series]] = None
    ) -> PerformanceMetrics:
        """
        Run backtest.

        Args:
            strategy: Trading strategy instance
            market_data: Dict of symbol: OHLCV DataFrame
            funding_data: Optional dict of symbol: funding rates

        Returns:
            Performance metrics
        """
        print(f"Starting backtest for {strategy.name}...")
        print(f"Initial capital: ${self.config.backtest.initial_capital:,.2f}")
        print(f"Date range: {list(market_data.values())[0].index[0]} to {list(market_data.values())[0].index[-1]}")

        # Initialize
        capital = self.config.backtest.initial_capital
        self.risk_manager.initialize(capital)
        self.position_sizer.update_portfolio_value(capital)

        # Get date range
        all_dates = sorted(set().union(*[df.index for df in market_data.values()]))

        # Initialize equity curve
        self.equity_curve = pd.Series(capital, index=[all_dates[0]])

        # Simulation loop
        for i, current_date in enumerate(all_dates[1:], 1):
            # Get current market data up to this point
            current_market = {}
            for symbol, df in market_data.items():
                current_market[symbol] = df[df.index <= current_date]

            # Skip if not enough data
            if any(len(df) < 50 for df in current_market.values()):
                continue

            # Generate signals
            signals = strategy.run(current_market, capital)

            # Process signals
            for signal in signals:
                self._process_signal(signal, current_date)

            # Update open positions
            current_prices = {
                symbol: df.loc[current_date, 'close']
                for symbol, df in market_data.items()
                if current_date in df.index
            }

            self._update_positions(current_prices, current_date)

            # Update equity
            unrealized_pnl = sum(
                pos.current_pnl(current_prices.get(pos.asset, pos.entry_price))
                for pos in self.risk_manager.open_positions.values()
            )

            current_equity = self.risk_manager.current_capital + unrealized_pnl
            self.equity_curve[current_date] = current_equity

            # Update position sizer
            self.position_sizer.update_portfolio_value(current_equity)

            # Progress
            if i % 1000 == 0:
                print(f"Progress: {i}/{len(all_dates)} ({i/len(all_dates)*100:.1f}%)")

        # Calculate metrics
        trades_df = self.risk_manager.get_trades_dataframe()
        metrics = calculate_metrics(
            self.equity_curve,
            trades_df,
            self.config.backtest.initial_capital
        )

        print(f"\nBacktest complete!")
        print(f"Total trades: {metrics.total_trades}")
        print(f"Final equity: ${self.equity_curve.iloc[-1]:,.2f}")

        return metrics

    def _process_signal(self, signal, current_date):
        """Process a trade signal."""
        # Check if we can open position
        can_open, violations = self.risk_manager.can_open_position(
            asset=signal.asset,
            direction=signal.direction,
            entry_price=signal.entry_price,
            size_usd=signal.position_size_usd,
            stop_loss=signal.stop_loss,
            leverage=signal.leverage
        )

        if not can_open:
            return

        # Apply slippage
        if signal.direction == 'LONG':
            entry_price = signal.entry_price * (1 + self.config.backtest.slippage_bps / 10000)
        else:
            entry_price = signal.entry_price * (1 - self.config.backtest.slippage_bps / 10000)

        # Apply fees
        fee = signal.position_size_usd * self.config.backtest.taker_fee
        self.risk_manager.current_capital -= fee

        # Open position
        success = self.risk_manager.open_position(
            asset=signal.asset,
            direction=signal.direction,
            entry_price=entry_price,
            size_units=signal.position_size_units,
            size_usd=signal.position_size_usd,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            leverage=signal.leverage,
            strategy=signal.strategy_name
        )

        if success:
            self.signals.append(signal)

    def _update_positions(self, current_prices: Dict, current_date):
        """Update and potentially close positions."""
        for asset, position in list(self.risk_manager.open_positions.items()):
            if asset not in current_prices:
                continue

            current_price = current_prices[asset]

            # Check stop loss
            should_close = False
            close_reason = ""

            if position.direction == 'LONG':
                if current_price <= position.stop_loss:
                    should_close = True
                    close_reason = "stop_loss"
                elif position.take_profit and current_price >= position.take_profit:
                    should_close = True
                    close_reason = "take_profit"
            else:  # SHORT
                if current_price >= position.stop_loss:
                    should_close = True
                    close_reason = "stop_loss"
                elif position.take_profit and current_price <= position.take_profit:
                    should_close = True
                    close_reason = "take_profit"

            if should_close:
                # Apply slippage and fees
                if position.direction == 'LONG':
                    exit_price = current_price * (1 - self.config.backtest.slippage_bps / 10000)
                else:
                    exit_price = current_price * (1 + self.config.backtest.slippage_bps / 10000)

                fee = position.size_usd * self.config.backtest.maker_fee
                self.risk_manager.current_capital -= fee

                # Close position
                trade = self.risk_manager.close_position(asset, exit_price, close_reason)
                if trade:
                    self.trades.append(trade)

    def get_results(self) -> Dict:
        """Get backtest results."""
        return {
            'equity_curve': self.equity_curve,
            'trades': self.risk_manager.get_trades_dataframe(),
            'signals': self.signals,
        }
