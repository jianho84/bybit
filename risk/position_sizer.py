"""
Position Sizing Module
=====================
Advanced position sizing algorithms including Kelly Criterion and volatility-based sizing.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class PositionSize:
    """Position size calculation result."""

    size_usd: float
    size_units: float
    risk_usd: float
    risk_pct: float
    leverage: float
    method: str


class PositionSizer:
    """
    Advanced position sizing for optimal risk-adjusted returns.
    Implements multiple sizing algorithms.
    """

    def __init__(
        self,
        portfolio_value: float,
        max_position_size: float = 0.25,
        max_leverage: float = 5.0
    ):
        """
        Initialize position sizer.

        Args:
            portfolio_value: Current portfolio value
            max_position_size: Max position as fraction of portfolio
            max_leverage: Maximum leverage allowed
        """
        self.portfolio_value = portfolio_value
        self.max_position_size = max_position_size
        self.max_leverage = max_leverage

    def fixed_fractional(
        self,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade: float = 0.01,
        leverage: float = 1.0
    ) -> PositionSize:
        """
        Fixed fractional position sizing.

        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_per_trade: Risk as fraction of portfolio (default 1%)
            leverage: Leverage to use

        Returns:
            PositionSize object
        """
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)

        if risk_per_unit == 0:
            return PositionSize(0, 0, 0, 0, leverage, "fixed_fractional")

        # Calculate position size based on risk
        risk_usd = self.portfolio_value * risk_per_trade
        position_size_units = risk_usd / risk_per_unit
        position_size_usd = position_size_units * entry_price

        # Apply leverage
        position_size_usd *= leverage

        # Apply max position constraint
        max_position_usd = self.portfolio_value * self.max_position_size
        if position_size_usd > max_position_usd:
            position_size_usd = max_position_usd
            position_size_units = position_size_usd / entry_price / leverage

        return PositionSize(
            size_usd=position_size_usd,
            size_units=position_size_units,
            risk_usd=risk_usd,
            risk_pct=risk_per_trade * 100,
            leverage=leverage,
            method="fixed_fractional"
        )

    def kelly_criterion(
        self,
        entry_price: float,
        stop_loss_price: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        kelly_fraction: float = 0.25,
        leverage: float = 1.0
    ) -> PositionSize:
        """
        Kelly Criterion position sizing.

        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade (as fraction)
            avg_loss: Average losing trade (as fraction, positive)
            kelly_fraction: Fraction of Kelly to use (default 0.25)
            leverage: Leverage to use

        Returns:
            PositionSize object
        """
        if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
            # Fall back to fixed fractional
            return self.fixed_fractional(
                entry_price, stop_loss_price, 0.01, leverage
            )

        # Kelly formula: f = (p * b - q) / b
        win_loss_ratio = avg_win / avg_loss
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio

        # Apply fractional Kelly for safety
        kelly_size = max(0, kelly * kelly_fraction)

        # Cap at max position size
        kelly_size = min(kelly_size, self.max_position_size)

        # Calculate position size
        position_size_usd = self.portfolio_value * kelly_size * leverage

        # Calculate risk
        risk_per_unit = abs(entry_price - stop_loss_price)
        position_size_units = position_size_usd / entry_price / leverage
        risk_usd = position_size_units * risk_per_unit

        return PositionSize(
            size_usd=position_size_usd,
            size_units=position_size_units,
            risk_usd=risk_usd,
            risk_pct=(risk_usd / self.portfolio_value) * 100,
            leverage=leverage,
            method="kelly_criterion"
        )

    def volatility_scaled(
        self,
        entry_price: float,
        stop_loss_price: float,
        current_atr: float,
        reference_atr: float,
        base_risk: float = 0.01,
        leverage: float = 1.0
    ) -> PositionSize:
        """
        Volatility-scaled position sizing (inverse ATR).

        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            current_atr: Current ATR value
            reference_atr: Reference/normal ATR value
            base_risk: Base risk per trade
            leverage: Leverage to use

        Returns:
            PositionSize object
        """
        if current_atr == 0 or reference_atr == 0:
            return self.fixed_fractional(
                entry_price, stop_loss_price, base_risk, leverage
            )

        # Scale risk inversely to volatility
        # Higher volatility = smaller position
        vol_adjustment = reference_atr / current_atr

        # Cap adjustment between 0.5x and 2x
        vol_adjustment = max(0.5, min(vol_adjustment, 2.0))

        # Adjusted risk
        adjusted_risk = base_risk * vol_adjustment

        # Calculate position
        risk_per_unit = abs(entry_price - stop_loss_price)
        risk_usd = self.portfolio_value * adjusted_risk
        position_size_units = risk_usd / risk_per_unit
        position_size_usd = position_size_units * entry_price * leverage

        # Apply max position constraint
        max_position_usd = self.portfolio_value * self.max_position_size
        if position_size_usd > max_position_usd:
            position_size_usd = max_position_usd
            position_size_units = position_size_usd / entry_price / leverage

        return PositionSize(
            size_usd=position_size_usd,
            size_units=position_size_units,
            risk_usd=risk_usd,
            risk_pct=adjusted_risk * 100,
            leverage=leverage,
            method="volatility_scaled"
        )

    def optimal_f(
        self,
        entry_price: float,
        trade_results: pd.Series,
        leverage: float = 1.0
    ) -> PositionSize:
        """
        Optimal f position sizing (Ralph Vince).

        Args:
            entry_price: Entry price
            trade_results: Historical trade P&L results
            leverage: Leverage to use

        Returns:
            PositionSize object
        """
        if len(trade_results) == 0:
            return PositionSize(0, 0, 0, 0, leverage, "optimal_f")

        # Find biggest loss
        biggest_loss = abs(trade_results.min())

        if biggest_loss == 0:
            return PositionSize(0, 0, 0, 0, leverage, "optimal_f")

        # Calculate optimal f
        f_values = np.linspace(0.01, 1.0, 100)
        twrs = []

        for f in f_values:
            units = f / biggest_loss
            hpr = 1 + (trade_results * units)
            twr = hpr.prod()
            twrs.append(twr)

        optimal_f = f_values[np.argmax(twrs)]

        # Apply safety factor (use 50% of optimal f)
        optimal_f = optimal_f * 0.5

        # Cap at max position size
        optimal_f = min(optimal_f, self.max_position_size)

        # Calculate position
        position_size_usd = self.portfolio_value * optimal_f * leverage
        position_size_units = position_size_usd / entry_price / leverage

        # Estimate risk (conservative: assume 50% of position can be lost)
        risk_usd = position_size_usd * 0.5

        return PositionSize(
            size_usd=position_size_usd,
            size_units=position_size_units,
            risk_usd=risk_usd,
            risk_pct=(risk_usd / self.portfolio_value) * 100,
            leverage=leverage,
            method="optimal_f"
        )

    def calculate(
        self,
        entry_price: float,
        stop_loss_price: float,
        method: str = "fixed_fractional",
        leverage: float = 1.0,
        **kwargs
    ) -> PositionSize:
        """
        Calculate position size using specified method.

        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            method: Sizing method (fixed_fractional, kelly_criterion, volatility_scaled, optimal_f)
            leverage: Leverage to use
            **kwargs: Additional parameters for specific methods

        Returns:
            PositionSize object
        """
        # Validate leverage
        leverage = min(leverage, self.max_leverage)

        if method == "fixed_fractional":
            return self.fixed_fractional(
                entry_price,
                stop_loss_price,
                kwargs.get('risk_per_trade', 0.01),
                leverage
            )

        elif method == "kelly_criterion":
            return self.kelly_criterion(
                entry_price,
                stop_loss_price,
                kwargs.get('win_rate', 0.5),
                kwargs.get('avg_win', 0.02),
                kwargs.get('avg_loss', 0.01),
                kwargs.get('kelly_fraction', 0.25),
                leverage
            )

        elif method == "volatility_scaled":
            return self.volatility_scaled(
                entry_price,
                stop_loss_price,
                kwargs.get('current_atr', 100),
                kwargs.get('reference_atr', 100),
                kwargs.get('base_risk', 0.01),
                leverage
            )

        elif method == "optimal_f":
            return self.optimal_f(
                entry_price,
                kwargs.get('trade_results', pd.Series()),
                leverage
            )

        else:
            raise ValueError(f"Unknown sizing method: {method}")

    def update_portfolio_value(self, new_value: float):
        """Update portfolio value."""
        self.portfolio_value = new_value
