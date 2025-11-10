"""
Helper Functions for Trading System
===================================
Utility functions for position sizing, performance metrics, and formatting.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime


def calculate_position_size(
    capital: float,
    entry_price: float,
    stop_loss_price: float,
    risk_per_trade: float = 0.01,
    max_position_size: float = 0.25
) -> Tuple[float, float]:
    """
    Calculate position size based on risk parameters.

    Args:
        capital: Total capital available
        entry_price: Entry price for the position
        stop_loss_price: Stop loss price
        risk_per_trade: Risk per trade as fraction of capital (default 1%)
        max_position_size: Maximum position size as fraction of capital

    Returns:
        Tuple of (position_size_usd, position_size_units)
    """
    # Calculate risk per unit
    risk_per_unit = abs(entry_price - stop_loss_price)

    if risk_per_unit == 0:
        raise ValueError("Stop loss cannot equal entry price")

    # Calculate position size based on risk
    risk_amount = capital * risk_per_trade
    position_size_units = risk_amount / risk_per_unit

    # Convert to USD value
    position_size_usd = position_size_units * entry_price

    # Apply maximum position size constraint
    max_position_usd = capital * max_position_size

    if position_size_usd > max_position_usd:
        position_size_usd = max_position_usd
        position_size_units = position_size_usd / entry_price

    return position_size_usd, position_size_units


def calculate_kelly_criterion(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    kelly_fraction: float = 0.25
) -> float:
    """
    Calculate Kelly Criterion for optimal position sizing.

    Args:
        win_rate: Historical win rate (0-1)
        avg_win: Average winning trade size
        avg_loss: Average losing trade size (positive number)
        kelly_fraction: Fraction of Kelly to use (default 0.25 for safety)

    Returns:
        Optimal position size as fraction of capital
    """
    if avg_loss == 0:
        return 0.0

    win_loss_ratio = avg_win / avg_loss

    # Kelly formula: f = (p * b - q) / b
    # where p = win rate, q = loss rate, b = win/loss ratio
    kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio

    # Apply fractional Kelly for safety
    kelly_size = max(0, kelly * kelly_fraction)

    return min(kelly_size, 0.25)  # Cap at 25% of capital


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Calculate annualized Sharpe ratio.

    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate (default 0)
        periods_per_year: Trading periods per year (252 for daily)

    Returns:
        Annualized Sharpe ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0

    excess_returns = returns - (risk_free_rate / periods_per_year)
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(periods_per_year)

    return sharpe


def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Calculate annualized Sortino ratio (uses downside deviation).

    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Trading periods per year

    Returns:
        Annualized Sortino ratio
    """
    if len(returns) == 0:
        return 0.0

    excess_returns = returns - (risk_free_rate / periods_per_year)
    downside_returns = excess_returns[excess_returns < 0]

    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0.0

    sortino = (
        (excess_returns.mean() / downside_returns.std()) *
        np.sqrt(periods_per_year)
    )

    return sortino


def calculate_max_drawdown(equity_curve: pd.Series) -> Tuple[float, int, int]:
    """
    Calculate maximum drawdown and duration.

    Args:
        equity_curve: Series of portfolio values over time

    Returns:
        Tuple of (max_drawdown_pct, start_idx, end_idx)
    """
    if len(equity_curve) == 0:
        return 0.0, 0, 0

    # Calculate running maximum
    running_max = equity_curve.expanding().max()

    # Calculate drawdown
    drawdown = (equity_curve - running_max) / running_max

    # Find maximum drawdown
    max_dd = drawdown.min()
    end_idx = drawdown.idxmin()

    # Find start of drawdown (last peak before max dd)
    start_idx = equity_curve[:end_idx].idxmax()

    return abs(max_dd), start_idx, end_idx


def calculate_calmar_ratio(
    returns: pd.Series,
    equity_curve: pd.Series,
    periods_per_year: int = 252
) -> float:
    """
    Calculate Calmar ratio (annual return / max drawdown).

    Args:
        returns: Series of returns
        equity_curve: Series of portfolio values
        periods_per_year: Trading periods per year

    Returns:
        Calmar ratio
    """
    if len(returns) == 0:
        return 0.0

    annual_return = returns.mean() * periods_per_year
    max_dd, _, _ = calculate_max_drawdown(equity_curve)

    if max_dd == 0:
        return 0.0

    return annual_return / max_dd


def calculate_var(
    returns: pd.Series,
    confidence: float = 0.95
) -> float:
    """
    Calculate Value at Risk (VaR).

    Args:
        returns: Series of returns
        confidence: Confidence level (default 0.95)

    Returns:
        VaR at given confidence level
    """
    if len(returns) == 0:
        return 0.0

    return np.percentile(returns, (1 - confidence) * 100)


def calculate_cvar(
    returns: pd.Series,
    confidence: float = 0.95
) -> float:
    """
    Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.

    Args:
        returns: Series of returns
        confidence: Confidence level

    Returns:
        CVaR at given confidence level
    """
    if len(returns) == 0:
        return 0.0

    var = calculate_var(returns, confidence)
    return returns[returns <= var].mean()


def calculate_performance_metrics(
    returns: pd.Series,
    equity_curve: pd.Series,
    trades: Optional[pd.DataFrame] = None
) -> Dict[str, float]:
    """
    Calculate comprehensive performance metrics.

    Args:
        returns: Series of returns
        equity_curve: Series of portfolio values
        trades: Optional DataFrame of trades

    Returns:
        Dictionary of performance metrics
    """
    metrics = {
        'total_return': (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100,
        'annual_return': returns.mean() * 252 * 100,
        'sharpe_ratio': calculate_sharpe_ratio(returns),
        'sortino_ratio': calculate_sortino_ratio(returns),
        'max_drawdown': calculate_max_drawdown(equity_curve)[0] * 100,
        'calmar_ratio': calculate_calmar_ratio(returns, equity_curve),
        'var_95': calculate_var(returns, 0.95) * 100,
        'cvar_95': calculate_cvar(returns, 0.95) * 100,
        'volatility': returns.std() * np.sqrt(252) * 100,
        'skewness': returns.skew(),
        'kurtosis': returns.kurtosis(),
    }

    # Add trade statistics if available
    if trades is not None and len(trades) > 0:
        winning_trades = trades[trades['pnl'] > 0]
        losing_trades = trades[trades['pnl'] <= 0]

        metrics.update({
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(trades) * 100 if len(trades) > 0 else 0,
            'avg_win': winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0,
            'avg_loss': losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0,
            'profit_factor': (
                abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum())
                if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0
                else 0
            ),
            'avg_trade_duration': trades['duration'].mean() if 'duration' in trades.columns else 0,
        })

    return metrics


def format_signal_output(
    strategy_name: str,
    asset: str,
    timeframe: str,
    direction: str,
    entry_zone: Tuple[float, float],
    trigger_condition: str,
    market_state: str,
    edge_rationale: str,
    risk_assessment: str,
    entry_price: float,
    stop_loss: float,
    take_profit: Optional[float],
    trailing_stop: Optional[str],
    position_size_pct: float,
    risk_pct: float,
    leverage: float = 1.0
) -> str:
    """
    Format trade signal output according to specification.

    Args:
        strategy_name: Name of the strategy
        asset: Trading pair
        timeframe: Timeframe
        direction: LONG or SHORT
        entry_zone: Tuple of (min, max) entry prices
        trigger_condition: Explanation of trigger
        market_state: Current market context
        edge_rationale: Statistical edge explanation
        risk_assessment: Risk factors
        entry_price: Entry price
        stop_loss: Stop loss price
        take_profit: Take profit price (if fixed)
        trailing_stop: Trailing stop description
        position_size_pct: Position size as % of portfolio
        risk_pct: Risk as % of portfolio
        leverage: Leverage used

    Returns:
        Formatted signal string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    output = f"""
{'='*70}
TRADE SIGNAL GENERATED
{'='*70}
Timestamp: {timestamp}
STRATEGY: {strategy_name}
ASSET: {asset}
TIMEFRAME: {timeframe}
DIRECTION: {direction}
ENTRY PRICE ZONE: {entry_zone[0]:.2f} - {entry_zone[1]:.2f}

JUSTIFICATION & MARKET CONTEXT:
{'─'*70}
1. Trigger Condition:
   {trigger_condition}

2. Market State:
   {market_state}

3. Edge Rationale:
   {edge_rationale}

4. Risk Assessment:
   {risk_assessment}

EXECUTION PARAMETERS:
{'─'*70}
- Entry:           ${entry_price:.2f} (Limit Order)
- Stop-Loss:       ${stop_loss:.2f} ({abs((entry_price - stop_loss) / entry_price * 100):.2f}%)
- Take-Profit:     {'$' + f'{take_profit:.2f}' if take_profit else 'N/A'}
- Trailing Stop:   {trailing_stop if trailing_stop else 'None'}
- Position Size:   {position_size_pct:.2f}% of portfolio
- Risk Amount:     {risk_pct:.2f}% of portfolio
- Leverage:        {leverage:.1f}x

{'='*70}
"""
    return output


def calculate_correlation_matrix(returns_dict: Dict[str, pd.Series]) -> pd.DataFrame:
    """
    Calculate correlation matrix for multiple assets.

    Args:
        returns_dict: Dictionary of asset: returns_series

    Returns:
        Correlation matrix DataFrame
    """
    df = pd.DataFrame(returns_dict)
    return df.corr()


def check_drawdown_breach(
    equity_curve: pd.Series,
    current_value: float,
    daily_limit: float = 0.05,
    weekly_limit: float = 0.10,
    monthly_limit: float = 0.15
) -> Tuple[bool, str]:
    """
    Check if drawdown limits have been breached.

    Args:
        equity_curve: Historical equity curve
        current_value: Current portfolio value
        daily_limit: Daily drawdown limit (default 5%)
        weekly_limit: Weekly drawdown limit (default 10%)
        monthly_limit: Monthly drawdown limit (default 15%)

    Returns:
        Tuple of (is_breached, breach_type)
    """
    if len(equity_curve) == 0:
        return False, ""

    # Check daily drawdown
    if len(equity_curve) >= 1:
        daily_peak = equity_curve.iloc[-1]
        daily_dd = (current_value - daily_peak) / daily_peak
        if abs(daily_dd) > daily_limit:
            return True, "daily"

    # Check weekly drawdown
    if len(equity_curve) >= 5:
        weekly_peak = equity_curve.iloc[-5:].max()
        weekly_dd = (current_value - weekly_peak) / weekly_peak
        if abs(weekly_dd) > weekly_limit:
            return True, "weekly"

    # Check monthly drawdown
    if len(equity_curve) >= 20:
        monthly_peak = equity_curve.iloc[-20:].max()
        monthly_dd = (current_value - monthly_peak) / monthly_peak
        if abs(monthly_dd) > monthly_limit:
            return True, "monthly"

    return False, ""


def scale_position_by_volatility(
    base_size: float,
    current_atr: float,
    reference_atr: float,
    max_adjustment: float = 2.0
) -> float:
    """
    Scale position size inversely to volatility using ATR.

    Args:
        base_size: Base position size
        current_atr: Current ATR value
        reference_atr: Reference/normal ATR value
        max_adjustment: Maximum adjustment multiplier

    Returns:
        Adjusted position size
    """
    if current_atr == 0 or reference_atr == 0:
        return base_size

    # Inverse scaling: lower volatility = larger position
    adjustment = reference_atr / current_atr

    # Cap adjustment
    adjustment = min(adjustment, max_adjustment)
    adjustment = max(adjustment, 1 / max_adjustment)

    return base_size * adjustment


def calculate_funding_rate_yield(
    funding_rate: float,
    periods_per_day: int = 3,
    days: int = 30
) -> float:
    """
    Calculate annualized yield from funding rate.

    Args:
        funding_rate: Current funding rate (as decimal)
        periods_per_day: Funding periods per day (default 3 for 8h)
        days: Projection days (default 30)

    Returns:
        Annualized yield
    """
    daily_rate = funding_rate * periods_per_day
    monthly_rate = daily_rate * days
    annual_rate = (1 + monthly_rate) ** (365 / days) - 1

    return annual_rate


def detect_regime_change(
    returns: pd.Series,
    window: int = 30,
    threshold: float = 2.0
) -> pd.Series:
    """
    Detect market regime changes using rolling volatility.

    Args:
        returns: Returns series
        window: Rolling window for volatility
        threshold: Z-score threshold for regime change

    Returns:
        Boolean series indicating regime changes
    """
    rolling_vol = returns.rolling(window=window).std()
    vol_mean = rolling_vol.mean()
    vol_std = rolling_vol.std()

    z_score = (rolling_vol - vol_mean) / vol_std

    regime_change = abs(z_score) > threshold

    return regime_change
