"""
Performance Metrics Module
=========================
Comprehensive performance analysis for backtests.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""

    # Returns
    total_return: float
    annual_return: float
    monthly_return: float

    # Risk-adjusted returns
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # Risk metrics
    max_drawdown: float
    max_drawdown_duration: int
    volatility: float
    downside_volatility: float

    # Value at Risk
    var_95: float
    cvar_95: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # Trade performance
    avg_win: float
    avg_loss: float
    profit_factor: float
    avg_trade_return: float

    # Duration
    avg_trade_duration: float
    max_trade_duration: float

    # Higher moments
    skewness: float
    kurtosis: float

    # Additional metrics
    recovery_factor: float
    ulcer_index: float

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'Total Return (%)': f"{self.total_return:.2f}",
            'Annual Return (%)': f"{self.annual_return:.2f}",
            'Monthly Return (%)': f"{self.monthly_return:.2f}",
            'Sharpe Ratio': f"{self.sharpe_ratio:.2f}",
            'Sortino Ratio': f"{self.sortino_ratio:.2f}",
            'Calmar Ratio': f"{self.calmar_ratio:.2f}",
            'Max Drawdown (%)': f"{self.max_drawdown:.2f}",
            'Volatility (%)': f"{self.volatility:.2f}",
            'VaR 95% (%)': f"{self.var_95:.2f}",
            'CVaR 95% (%)': f"{self.cvar_95:.2f}",
            'Total Trades': self.total_trades,
            'Win Rate (%)': f"{self.win_rate:.2f}",
            'Profit Factor': f"{self.profit_factor:.2f}",
            'Avg Win (%)': f"{self.avg_win:.2f}",
            'Avg Loss (%)': f"{self.avg_loss:.2f}",
            'Recovery Factor': f"{self.recovery_factor:.2f}",
        }

    def __str__(self) -> str:
        """Format for display."""
        output = "\n" + "="*60 + "\n"
        output += "PERFORMANCE METRICS\n"
        output += "="*60 + "\n\n"

        output += "Returns:\n"
        output += f"  Total Return:        {self.total_return:>10.2f}%\n"
        output += f"  Annual Return:       {self.annual_return:>10.2f}%\n"
        output += f"  Monthly Return:      {self.monthly_return:>10.2f}%\n\n"

        output += "Risk-Adjusted Returns:\n"
        output += f"  Sharpe Ratio:        {self.sharpe_ratio:>10.2f}\n"
        output += f"  Sortino Ratio:       {self.sortino_ratio:>10.2f}\n"
        output += f"  Calmar Ratio:        {self.calmar_ratio:>10.2f}\n\n"

        output += "Risk Metrics:\n"
        output += f"  Max Drawdown:        {self.max_drawdown:>10.2f}%\n"
        output += f"  Volatility (Ann.):   {self.volatility:>10.2f}%\n"
        output += f"  VaR 95%:             {self.var_95:>10.2f}%\n"
        output += f"  CVaR 95%:            {self.cvar_95:>10.2f}%\n\n"

        output += "Trade Statistics:\n"
        output += f"  Total Trades:        {self.total_trades:>10}\n"
        output += f"  Winning Trades:      {self.winning_trades:>10}\n"
        output += f"  Losing Trades:       {self.losing_trades:>10}\n"
        output += f"  Win Rate:            {self.win_rate:>10.2f}%\n"
        output += f"  Profit Factor:       {self.profit_factor:>10.2f}\n\n"

        output += "Trade Performance:\n"
        output += f"  Avg Win:             {self.avg_win:>10.2f}%\n"
        output += f"  Avg Loss:            {self.avg_loss:>10.2f}%\n"
        output += f"  Avg Duration:        {self.avg_trade_duration:>10.1f}h\n\n"

        output += "="*60 + "\n"

        return output


def calculate_metrics(
    equity_curve: pd.Series,
    trades: pd.DataFrame,
    initial_capital: float,
    risk_free_rate: float = 0.0
) -> PerformanceMetrics:
    """
    Calculate comprehensive performance metrics.

    Args:
        equity_curve: Series of portfolio values over time
        trades: DataFrame of trade results
        initial_capital: Starting capital
        risk_free_rate: Annual risk-free rate

    Returns:
        PerformanceMetrics object
    """
    # Calculate returns
    returns = equity_curve.pct_change().dropna()

    # Total return
    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100

    # Annualized return
    days = (equity_curve.index[-1] - equity_curve.index[0]).days
    years = days / 365.25
    annual_return = ((equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (1/years) - 1) * 100 if years > 0 else 0

    # Monthly return
    monthly_return = annual_return / 12

    # Sharpe ratio
    excess_returns = returns - (risk_free_rate / 252)
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() > 0 else 0

    # Sortino ratio
    downside_returns = excess_returns[excess_returns < 0]
    sortino = (
        (excess_returns.mean() / downside_returns.std()) * np.sqrt(252)
        if len(downside_returns) > 0 and downside_returns.std() > 0
        else 0
    )

    # Max drawdown
    running_max = equity_curve.expanding().max()
    drawdown = (equity_curve - running_max) / running_max
    max_dd = abs(drawdown.min()) * 100

    # Max drawdown duration
    dd_end = drawdown.idxmin()
    dd_start = equity_curve[:dd_end].idxmax()
    max_dd_duration = (dd_end - dd_start).days if dd_end != dd_start else 0

    # Calmar ratio
    calmar = annual_return / max_dd if max_dd > 0 else 0

    # Volatility
    volatility = returns.std() * np.sqrt(252) * 100
    downside_vol = downside_returns.std() * np.sqrt(252) * 100 if len(downside_returns) > 0 else 0

    # VaR and CVaR
    var_95 = np.percentile(returns, 5) * 100
    cvar_95 = returns[returns <= np.percentile(returns, 5)].mean() * 100 if len(returns) > 0 else 0

    # Trade statistics
    if len(trades) > 0:
        total_trades = len(trades)
        winning_trades = len(trades[trades['pnl'] > 0])
        losing_trades = len(trades[trades['pnl'] <= 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        wins = trades[trades['pnl'] > 0]['pnl_pct']
        losses = trades[trades['pnl'] <= 0]['pnl_pct']

        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0

        total_wins = wins.sum() if len(wins) > 0 else 0
        total_losses = abs(losses.sum()) if len(losses) > 0 else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        avg_trade_return = trades['pnl_pct'].mean()

        if 'duration' in trades.columns:
            avg_duration = trades['duration'].mean()
            max_duration = trades['duration'].max()
        else:
            avg_duration = 0
            max_duration = 0
    else:
        total_trades = winning_trades = losing_trades = 0
        win_rate = avg_win = avg_loss = profit_factor = avg_trade_return = 0
        avg_duration = max_duration = 0

    # Higher moments
    skewness = returns.skew()
    kurtosis = returns.kurtosis()

    # Recovery factor
    recovery_factor = abs(total_return / max_dd) if max_dd > 0 else 0

    # Ulcer Index (measure of drawdown depth and duration)
    squared_dd = (drawdown ** 2).sum()
    ulcer = np.sqrt(squared_dd / len(drawdown)) * 100 if len(drawdown) > 0 else 0

    return PerformanceMetrics(
        total_return=total_return,
        annual_return=annual_return,
        monthly_return=monthly_return,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        calmar_ratio=calmar,
        max_drawdown=max_dd,
        max_drawdown_duration=max_dd_duration,
        volatility=volatility,
        downside_volatility=downside_vol,
        var_95=var_95,
        cvar_95=cvar_95,
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        avg_trade_return=avg_trade_return,
        avg_trade_duration=avg_duration,
        max_trade_duration=max_duration,
        skewness=skewness,
        kurtosis=kurtosis,
        recovery_factor=recovery_factor,
        ulcer_index=ulcer,
    )
