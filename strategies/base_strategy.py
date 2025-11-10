"""
Base Strategy Class
==================
Abstract base class for all trading strategies.
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from utils.indicators import TechnicalIndicators
from utils.signal_generator import SignalGenerator, TradeSignal
from utils.helpers import calculate_performance_metrics
from risk.position_sizer import PositionSizer
from risk.risk_manager import RiskManager


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    Defines the interface and common functionality.
    """

    def __init__(
        self,
        config,
        risk_manager: Optional[RiskManager] = None,
        position_sizer: Optional[PositionSizer] = None
    ):
        """
        Initialize base strategy.

        Args:
            config: Strategy configuration object
            risk_manager: Risk manager instance
            position_sizer: Position sizer instance
        """
        self.config = config
        self.risk_manager = risk_manager
        self.position_sizer = position_sizer
        self.signal_generator = SignalGenerator()

        # Technical indicators helper
        self.indicators = TechnicalIndicators()

        # Performance tracking
        self.signals_generated = []
        self.trades = []
        self.equity_curve = pd.Series(dtype=float)

        # Strategy metadata
        self.name = self.__class__.__name__
        self.is_initialized = False

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> List[TradeSignal]:
        """
        Generate trading signals from market data.

        Args:
            df: OHLCV DataFrame with market data

        Returns:
            List of TradeSignal objects
        """
        pass

    @abstractmethod
    def calculate_entry_exit(
        self,
        df: pd.DataFrame,
        signal_idx: int,
        direction: str
    ) -> Dict:
        """
        Calculate entry, stop-loss, and take-profit levels.

        Args:
            df: OHLCV DataFrame
            signal_idx: Index where signal was generated
            direction: LONG or SHORT

        Returns:
            Dictionary with entry, stop_loss, take_profit
        """
        pass

    def validate_signal(
        self,
        df: pd.DataFrame,
        signal_idx: int,
        direction: str
    ) -> bool:
        """
        Validate if signal meets quality criteria.

        Args:
            df: OHLCV DataFrame
            signal_idx: Index where signal was generated
            direction: LONG or SHORT

        Returns:
            True if signal is valid
        """
        # Default validation (can be overridden)
        # Check if we have enough historical data
        if signal_idx < 50:
            return False

        # Check if price data is valid
        if df.loc[signal_idx, 'close'] <= 0:
            return False

        return True

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        leverage: float = 1.0,
        **kwargs
    ) -> Dict:
        """
        Calculate position size using position sizer.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            leverage: Leverage to use
            **kwargs: Additional parameters for sizing

        Returns:
            Dictionary with position sizing details
        """
        if self.position_sizer is None:
            return {
                'size_usd': 0,
                'size_units': 0,
                'risk_pct': 0,
            }

        # Use configured sizing method or default to fixed fractional
        method = kwargs.get('method', 'fixed_fractional')

        position = self.position_sizer.calculate(
            entry_price=entry_price,
            stop_loss_price=stop_loss,
            method=method,
            leverage=leverage,
            **kwargs
        )

        return {
            'size_usd': position.size_usd,
            'size_units': position.size_units,
            'risk_usd': position.risk_usd,
            'risk_pct': position.risk_pct,
            'leverage': position.leverage,
        }

    def format_signal(
        self,
        asset: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: Optional[float],
        trailing_stop_desc: Optional[str],
        trigger_condition: str,
        market_state: str,
        edge_rationale: str,
        risk_assessment: str,
        position_sizing: Dict,
        expected_win_rate: float = 0.0,
        expected_profit_factor: float = 0.0,
        confidence: float = 0.0
    ) -> TradeSignal:
        """
        Format a trade signal using the signal generator.

        Args:
            asset: Trading pair
            direction: LONG or SHORT
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            trailing_stop_desc: Trailing stop description
            trigger_condition: What triggered the signal
            market_state: Current market context
            edge_rationale: Why this trade has an edge
            risk_assessment: What could go wrong
            position_sizing: Position sizing dict
            expected_win_rate: Historical win rate
            expected_profit_factor: Historical profit factor
            confidence: Confidence level (0-1)

        Returns:
            TradeSignal object
        """
        signal = self.signal_generator.create_signal(
            strategy_name=self.name,
            asset=asset,
            timeframe=self.config.timeframe,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop_desc=trailing_stop_desc,
            position_size_pct=(
                position_sizing['size_usd'] / self.position_sizer.portfolio_value * 100
                if self.position_sizer else 0
            ),
            position_size_usd=position_sizing.get('size_usd', 0),
            position_size_units=position_sizing.get('size_units', 0),
            risk_pct=position_sizing.get('risk_pct', 0),
            leverage=position_sizing.get('leverage', 1.0),
            trigger_condition=trigger_condition,
            market_state=market_state,
            edge_rationale=edge_rationale,
            risk_assessment=risk_assessment,
            confidence=confidence,
            expected_win_rate=expected_win_rate,
            expected_profit_factor=expected_profit_factor,
        )

        return signal

    def run(
        self,
        market_data: Dict[str, pd.DataFrame],
        portfolio_value: float
    ) -> List[TradeSignal]:
        """
        Run strategy on market data.

        Args:
            market_data: Dict of asset: OHLCV DataFrame
            portfolio_value: Current portfolio value

        Returns:
            List of generated signals
        """
        all_signals = []

        # Update position sizer portfolio value
        if self.position_sizer:
            self.position_sizer.update_portfolio_value(portfolio_value)

        # Process each asset
        for asset, df in market_data.items():
            if asset not in self.config.assets:
                continue

            signals = self.generate_signals(df)
            all_signals.extend(signals)

        self.signals_generated.extend(all_signals)
        return all_signals

    def get_performance_metrics(self) -> Dict:
        """
        Calculate strategy performance metrics.

        Returns:
            Dictionary of performance metrics
        """
        if len(self.trades) == 0:
            return {}

        trades_df = pd.DataFrame(self.trades)
        returns = trades_df['pnl_pct'] / 100

        metrics = calculate_performance_metrics(
            returns=returns,
            equity_curve=self.equity_curve,
            trades=trades_df
        )

        return metrics

    def get_signals_dataframe(self) -> pd.DataFrame:
        """Get all generated signals as DataFrame."""
        return self.signal_generator.export_signals_to_df()

    def reset(self):
        """Reset strategy state."""
        self.signals_generated = []
        self.trades = []
        self.equity_curve = pd.Series(dtype=float)
        self.signal_generator.clear_history()

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} Strategy"
