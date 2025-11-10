"""
Risk Manager Module
==================
Comprehensive risk management system with multi-level controls.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class RiskViolationType(Enum):
    """Types of risk violations."""
    MAX_POSITION_SIZE = "max_position_size"
    MAX_LEVERAGE = "max_leverage"
    MAX_CORRELATION = "max_correlation"
    MAX_DRAWDOWN_DAILY = "max_drawdown_daily"
    MAX_DRAWDOWN_WEEKLY = "max_drawdown_weekly"
    MAX_DRAWDOWN_MONTHLY = "max_drawdown_monthly"
    MAX_OPEN_POSITIONS = "max_open_positions"
    INSUFFICIENT_LIQUIDITY = "insufficient_liquidity"


@dataclass
class Position:
    """Open position data structure."""
    asset: str
    direction: str  # LONG or SHORT
    entry_price: float
    size_units: float
    size_usd: float
    stop_loss: float
    take_profit: Optional[float]
    leverage: float
    entry_time: datetime
    strategy: str

    def current_pnl(self, current_price: float) -> float:
        """Calculate current P&L."""
        if self.direction == "LONG":
            pnl = (current_price - self.entry_price) * self.size_units
        else:
            pnl = (self.entry_price - current_price) * self.size_units
        return pnl

    def current_pnl_pct(self, current_price: float) -> float:
        """Calculate current P&L percentage."""
        if self.size_usd == 0:
            return 0.0
        return (self.current_pnl(current_price) / self.size_usd) * 100


@dataclass
class RiskMetrics:
    """Current risk metrics."""
    portfolio_value: float
    total_position_value: float
    position_utilization: float  # % of capital in positions
    current_leverage: float
    unrealized_pnl: float
    realized_pnl_today: float
    daily_drawdown: float
    weekly_drawdown: float
    monthly_drawdown: float
    open_positions: int
    risk_violations: List[RiskViolationType] = field(default_factory=list)


class RiskManager:
    """
    Comprehensive risk management system.
    Enforces position limits, leverage limits, drawdown controls, and correlation limits.
    """

    def __init__(self, config):
        """
        Initialize risk manager.

        Args:
            config: RiskConfig object
        """
        self.config = config

        # Portfolio tracking
        self.initial_capital = 0.0
        self.current_capital = 0.0
        self.equity_curve = pd.Series(dtype=float)

        # Position tracking
        self.open_positions: Dict[str, Position] = {}

        # Historical data for drawdown calculation
        self.daily_peak = 0.0
        self.weekly_peak = 0.0
        self.monthly_peak = 0.0

        # Performance tracking
        self.trades_history = []

    def initialize(self, initial_capital: float):
        """
        Initialize risk manager with starting capital.

        Args:
            initial_capital: Starting portfolio value
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.daily_peak = initial_capital
        self.weekly_peak = initial_capital
        self.monthly_peak = initial_capital

        # Initialize equity curve
        self.equity_curve = pd.Series([initial_capital], index=[datetime.now()])

    def can_open_position(
        self,
        asset: str,
        direction: str,
        entry_price: float,
        size_usd: float,
        stop_loss: float,
        leverage: float,
        current_prices: Optional[Dict[str, float]] = None
    ) -> Tuple[bool, List[RiskViolationType]]:
        """
        Check if a new position can be opened based on risk rules.

        Args:
            asset: Trading pair
            direction: LONG or SHORT
            entry_price: Entry price
            size_usd: Position size in USD
            stop_loss: Stop loss price
            leverage: Leverage to use
            current_prices: Dict of asset: current_price for existing positions

        Returns:
            Tuple of (can_open, violations)
        """
        violations = []

        # Check max open positions
        if len(self.open_positions) >= self.config.max_open_positions:
            violations.append(RiskViolationType.MAX_OPEN_POSITIONS)

        # Check position size limit
        position_pct = size_usd / self.current_capital
        if position_pct > self.config.max_position_size:
            violations.append(RiskViolationType.MAX_POSITION_SIZE)

        # Check leverage limit
        if leverage > self.config.max_leverage:
            violations.append(RiskViolationType.MAX_LEVERAGE)

        # Check drawdown limits
        if current_prices:
            current_equity = self._calculate_current_equity(current_prices)
            dd_daily = (current_equity - self.daily_peak) / self.daily_peak
            dd_weekly = (current_equity - self.weekly_peak) / self.weekly_peak
            dd_monthly = (current_equity - self.monthly_peak) / self.monthly_peak

            if abs(dd_daily) >= self.config.max_daily_drawdown:
                violations.append(RiskViolationType.MAX_DRAWDOWN_DAILY)

            if abs(dd_weekly) >= self.config.max_weekly_drawdown:
                violations.append(RiskViolationType.MAX_DRAWDOWN_WEEKLY)

            if abs(dd_monthly) >= self.config.max_monthly_drawdown:
                violations.append(RiskViolationType.MAX_DRAWDOWN_MONTHLY)

        # Check correlation if there are existing positions
        if len(self.open_positions) > 0:
            correlated_positions = self._count_correlated_positions(asset)
            if correlated_positions >= self.config.max_correlated_positions:
                violations.append(RiskViolationType.MAX_CORRELATION)

        can_open = len(violations) == 0
        return can_open, violations

    def open_position(
        self,
        asset: str,
        direction: str,
        entry_price: float,
        size_units: float,
        size_usd: float,
        stop_loss: float,
        take_profit: Optional[float],
        leverage: float,
        strategy: str
    ) -> bool:
        """
        Open a new position.

        Args:
            asset: Trading pair
            direction: LONG or SHORT
            entry_price: Entry price
            size_units: Position size in units
            size_usd: Position size in USD
            stop_loss: Stop loss price
            take_profit: Take profit price (optional)
            leverage: Leverage used
            strategy: Strategy name

        Returns:
            True if position opened successfully
        """
        # Check if position already exists
        if asset in self.open_positions:
            return False

        # Create position
        position = Position(
            asset=asset,
            direction=direction,
            entry_price=entry_price,
            size_units=size_units,
            size_usd=size_usd,
            stop_loss=stop_loss,
            take_profit=take_profit,
            leverage=leverage,
            entry_time=datetime.now(),
            strategy=strategy
        )

        self.open_positions[asset] = position
        return True

    def close_position(
        self,
        asset: str,
        exit_price: float,
        reason: str = "manual"
    ) -> Optional[Dict]:
        """
        Close an existing position.

        Args:
            asset: Trading pair
            exit_price: Exit price
            reason: Reason for closing

        Returns:
            Trade result dictionary or None
        """
        if asset not in self.open_positions:
            return None

        position = self.open_positions[asset]

        # Calculate P&L
        pnl = position.current_pnl(exit_price)
        pnl_pct = position.current_pnl_pct(exit_price)

        # Record trade
        trade_result = {
            'asset': asset,
            'strategy': position.strategy,
            'direction': position.direction,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'size_units': position.size_units,
            'size_usd': position.size_usd,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'leverage': position.leverage,
            'entry_time': position.entry_time,
            'exit_time': datetime.now(),
            'duration': (datetime.now() - position.entry_time).total_seconds() / 3600,
            'reason': reason
        }

        self.trades_history.append(trade_result)

        # Update capital
        self.current_capital += pnl

        # Remove position
        del self.open_positions[asset]

        return trade_result

    def update_equity_curve(self, current_prices: Dict[str, float]):
        """
        Update equity curve with current prices.

        Args:
            current_prices: Dict of asset: current_price
        """
        current_equity = self._calculate_current_equity(current_prices)

        # Update equity curve
        self.equity_curve[datetime.now()] = current_equity

        # Update peaks for drawdown calculation
        if current_equity > self.daily_peak:
            self.daily_peak = current_equity

        # Update weekly peak (reset every Monday)
        if datetime.now().weekday() == 0:
            self.weekly_peak = current_equity
        elif current_equity > self.weekly_peak:
            self.weekly_peak = current_equity

        # Update monthly peak (reset on 1st of month)
        if datetime.now().day == 1:
            self.monthly_peak = current_equity
        elif current_equity > self.monthly_peak:
            self.monthly_peak = current_equity

    def get_risk_metrics(self, current_prices: Dict[str, float]) -> RiskMetrics:
        """
        Calculate current risk metrics.

        Args:
            current_prices: Dict of asset: current_price

        Returns:
            RiskMetrics object
        """
        current_equity = self._calculate_current_equity(current_prices)

        # Calculate position utilization
        total_position_value = sum(pos.size_usd for pos in self.open_positions.values())
        position_utilization = (
            (total_position_value / current_equity) * 100
            if current_equity > 0 else 0
        )

        # Calculate average leverage
        if len(self.open_positions) > 0:
            avg_leverage = sum(
                pos.leverage * pos.size_usd
                for pos in self.open_positions.values()
            ) / total_position_value
        else:
            avg_leverage = 0.0

        # Calculate unrealized P&L
        unrealized_pnl = sum(
            pos.current_pnl(current_prices.get(pos.asset, pos.entry_price))
            for pos in self.open_positions.values()
        )

        # Calculate realized P&L today
        today = datetime.now().date()
        realized_pnl_today = sum(
            trade['pnl']
            for trade in self.trades_history
            if trade['exit_time'].date() == today
        )

        # Calculate drawdowns
        dd_daily = (current_equity - self.daily_peak) / self.daily_peak
        dd_weekly = (current_equity - self.weekly_peak) / self.weekly_peak
        dd_monthly = (current_equity - self.monthly_peak) / self.monthly_peak

        # Check for violations
        violations = []
        if abs(dd_daily) >= self.config.max_daily_drawdown:
            violations.append(RiskViolationType.MAX_DRAWDOWN_DAILY)
        if abs(dd_weekly) >= self.config.max_weekly_drawdown:
            violations.append(RiskViolationType.MAX_DRAWDOWN_WEEKLY)
        if abs(dd_monthly) >= self.config.max_monthly_drawdown:
            violations.append(RiskViolationType.MAX_DRAWDOWN_MONTHLY)

        return RiskMetrics(
            portfolio_value=current_equity,
            total_position_value=total_position_value,
            position_utilization=position_utilization,
            current_leverage=avg_leverage,
            unrealized_pnl=unrealized_pnl,
            realized_pnl_today=realized_pnl_today,
            daily_drawdown=abs(dd_daily) * 100,
            weekly_drawdown=abs(dd_weekly) * 100,
            monthly_drawdown=abs(dd_monthly) * 100,
            open_positions=len(self.open_positions),
            risk_violations=violations
        )

    def should_stop_trading(self, current_prices: Dict[str, float]) -> bool:
        """
        Check if trading should be stopped due to risk limits.

        Args:
            current_prices: Dict of asset: current_price

        Returns:
            True if trading should stop
        """
        metrics = self.get_risk_metrics(current_prices)

        # Stop if any major drawdown limit breached
        return len(metrics.risk_violations) > 0

    def _calculate_current_equity(self, current_prices: Dict[str, float]) -> float:
        """Calculate current equity including unrealized P&L."""
        unrealized_pnl = sum(
            pos.current_pnl(current_prices.get(pos.asset, pos.entry_price))
            for pos in self.open_positions.values()
        )
        return self.current_capital + unrealized_pnl

    def _count_correlated_positions(self, asset: str) -> int:
        """
        Count number of highly correlated positions.

        Args:
            asset: Asset to check correlation for

        Returns:
            Number of correlated positions
        """
        # Simplified correlation check based on base asset
        # BTC/USDT correlates with ETH/USDT, etc.
        base_asset = asset.split('/')[0]

        # Define correlation groups
        major_correlation_groups = [
            {'BTC', 'ETH'},  # Major cryptos
            {'SOL', 'AVAX', 'MATIC'},  # Layer 1s
            {'UNI', 'AAVE', 'SNX'},  # DeFi
        ]

        # Find which group this asset belongs to
        asset_group = None
        for group in major_correlation_groups:
            if base_asset in group:
                asset_group = group
                break

        if asset_group is None:
            return 0

        # Count positions in same group
        count = sum(
            1 for pos in self.open_positions.values()
            if pos.asset.split('/')[0] in asset_group
        )

        return count

    def get_trades_dataframe(self) -> pd.DataFrame:
        """Get trades history as DataFrame."""
        if not self.trades_history:
            return pd.DataFrame()
        return pd.DataFrame(self.trades_history)

    def get_equity_curve(self) -> pd.Series:
        """Get equity curve."""
        return self.equity_curve

    def reset(self):
        """Reset risk manager."""
        self.open_positions = {}
        self.trades_history = []
        self.current_capital = self.initial_capital
        self.daily_peak = self.initial_capital
        self.weekly_peak = self.initial_capital
        self.monthly_peak = self.initial_capital
