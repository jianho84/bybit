"""
Journal Manager
===============
High-level interface for trade journaling.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd

from journal.database import TradeDatabase
from utils.signal_generator import TradeSignal


class JournalManager:
    """
    High-level journal manager.

    Automatically logs:
    - All generated signals
    - Trade entries and exits
    - Daily performance summaries
    """

    def __init__(self, db_path: str = "data/trading_journal.db"):
        """
        Initialize journal manager.

        Args:
            db_path: Path to SQLite database
        """
        self.db = TradeDatabase(db_path)
        self.signal_id_map = {}  # Maps signal objects to database IDs

    def log_signal(self, signal: TradeSignal) -> int:
        """
        Log a trading signal.

        Args:
            signal: TradeSignal object

        Returns:
            Signal ID in database
        """
        signal_data = {
            'timestamp': signal.timestamp.isoformat(),
            'strategy': signal.strategy_name,
            'asset': signal.asset,
            'timeframe': signal.timeframe,
            'direction': signal.direction,
            'entry_price': signal.entry_price,
            'entry_zone_min': signal.entry_zone_min,
            'entry_zone_max': signal.entry_zone_max,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'position_size_usd': signal.position_size_usd,
            'position_size_units': signal.position_size_units,
            'position_size_pct': signal.position_size_pct,
            'risk_pct': signal.risk_pct,
            'leverage': signal.leverage,
            'confidence': signal.confidence,
            'expected_win_rate': signal.expected_win_rate,
            'expected_profit_factor': signal.expected_profit_factor,
            'trigger_condition': signal.trigger_condition,
            'market_state': signal.market_state,
            'edge_rationale': signal.edge_rationale,
            'risk_assessment': signal.risk_assessment,
            'status': 'generated'
        }

        signal_id = self.db.log_signal(signal_data)

        # Store mapping
        self.signal_id_map[id(signal)] = signal_id

        return signal_id

    def log_trade_entry(
        self,
        signal: Optional[TradeSignal],
        entry_time: datetime,
        entry_price: float,
        entry_size_units: float,
        entry_size_usd: float,
        entry_fee: float = 0,
        slippage_bps: float = 0,
        **kwargs
    ) -> int:
        """
        Log trade entry.

        Args:
            signal: Original signal (optional)
            entry_time: Entry timestamp
            entry_price: Actual entry price
            entry_size_units: Position size in units
            entry_size_usd: Position size in USD
            entry_fee: Entry fee paid
            slippage_bps: Slippage in basis points
            **kwargs: Additional trade details

        Returns:
            Trade ID
        """
        signal_id = None
        if signal:
            signal_id = self.signal_id_map.get(id(signal))

        trade_data = {
            'signal_id': signal_id,
            'strategy': signal.strategy_name if signal else kwargs.get('strategy', ''),
            'asset': signal.asset if signal else kwargs.get('asset', ''),
            'direction': signal.direction if signal else kwargs.get('direction', ''),
            'entry_time': entry_time.isoformat() if isinstance(entry_time, datetime) else entry_time,
            'entry_price': entry_price,
            'entry_size_units': entry_size_units,
            'entry_size_usd': entry_size_usd,
            'entry_fee': entry_fee,
            'entry_slippage_bps': slippage_bps,
            'leverage': signal.leverage if signal else kwargs.get('leverage', 1.0),
            'stop_loss': signal.stop_loss if signal else kwargs.get('stop_loss'),
            'take_profit': signal.take_profit if signal else kwargs.get('take_profit'),
        }

        trade_id = self.db.log_trade(trade_data)
        return trade_id

    def log_trade_exit(
        self,
        trade_id: int,
        exit_time: datetime,
        exit_price: float,
        exit_reason: str,
        exit_fee: float = 0,
        slippage_bps: float = 0
    ):
        """
        Log trade exit and calculate P&L.

        Args:
            trade_id: Trade ID from log_trade_entry
            exit_time: Exit timestamp
            exit_price: Actual exit price
            exit_reason: Reason for exit
            exit_fee: Exit fee paid
            slippage_bps: Exit slippage in bps
        """
        # Get trade data
        trades_df = self.db.get_trades()
        trade = trades_df[trades_df['trade_id'] == trade_id].iloc[0]

        # Calculate P&L
        entry_price = trade['entry_price']
        size_units = trade['entry_size_units']
        direction = trade['direction']

        if direction == 'LONG':
            pnl = (exit_price - entry_price) * size_units
        else:  # SHORT
            pnl = (entry_price - exit_price) * size_units

        pnl_pct = (pnl / trade['entry_size_usd']) * 100

        # After fees
        total_fees = trade['entry_fee'] + exit_fee
        pnl_after_fees = pnl - total_fees

        # Duration
        entry_dt = pd.to_datetime(trade['entry_time'])
        exit_dt = pd.to_datetime(exit_time)
        duration_hours = (exit_dt - entry_dt).total_seconds() / 3600

        # Update trade
        updates = {
            'exit_time': exit_time.isoformat() if isinstance(exit_time, datetime) else exit_time,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'exit_fee': exit_fee,
            'exit_slippage_bps': slippage_bps,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'pnl_after_fees': pnl_after_fees,
            'duration_hours': duration_hours
        }

        self.db.update_trade(trade_id, updates)

    def log_backtest_results(
        self,
        strategy_name: str,
        signals: list,
        trades_df: pd.DataFrame
    ):
        """
        Log entire backtest results.

        Args:
            strategy_name: Strategy name
            signals: List of TradeSignal objects
            trades_df: DataFrame of trade results
        """
        print(f"Logging {len(signals)} signals to journal...")

        # Log all signals
        for signal in signals:
            self.log_signal(signal)

        print(f"Logging {len(trades_df)} trades to journal...")

        # Log all trades
        for _, trade in trades_df.iterrows():
            trade_data = {
                'strategy': strategy_name,
                'asset': trade.get('asset', ''),
                'direction': trade.get('direction', ''),
                'entry_time': trade.get('entry_time'),
                'entry_price': trade.get('entry_price', 0),
                'entry_size_units': trade.get('size_units', 0),
                'entry_size_usd': trade.get('size_usd', 0),
                'exit_time': trade.get('exit_time'),
                'exit_price': trade.get('exit_price', 0),
                'exit_reason': trade.get('reason', ''),
                'pnl': trade.get('pnl', 0),
                'pnl_pct': trade.get('pnl_pct', 0),
                'duration_hours': trade.get('duration', 0),
                'leverage': trade.get('leverage', 1.0),
            }

            self.db.log_trade(trade_data)

        print("✓ Backtest results logged successfully!")

    def get_summary(
        self,
        strategy: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get performance summary.

        Args:
            strategy: Filter by strategy
            days: Number of days to include

        Returns:
            Summary dictionary
        """
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - pd.Timedelta(days=days)

        # Get trades
        trades_df = self.db.get_trades(
            strategy=strategy,
            start_date=start_date.isoformat()
        )

        if len(trades_df) == 0:
            return {'message': 'No trades found'}

        # Calculate summary
        summary = {
            'period_days': days,
            'total_trades': len(trades_df),
            'winning_trades': len(trades_df[trades_df['pnl'] > 0]),
            'losing_trades': len(trades_df[trades_df['pnl'] <= 0]),
            'win_rate': len(trades_df[trades_df['pnl'] > 0]) / len(trades_df) * 100,
            'total_pnl': trades_df['pnl'].sum(),
            'total_pnl_pct': trades_df['pnl_pct'].mean(),
            'avg_win': trades_df[trades_df['pnl'] > 0]['pnl_pct'].mean() if len(trades_df[trades_df['pnl'] > 0]) > 0 else 0,
            'avg_loss': trades_df[trades_df['pnl'] <= 0]['pnl_pct'].mean() if len(trades_df[trades_df['pnl'] <= 0]) > 0 else 0,
            'best_trade': trades_df['pnl_pct'].max(),
            'worst_trade': trades_df['pnl_pct'].min(),
            'avg_duration_hours': trades_df['duration_hours'].mean(),
        }

        # Profit factor
        wins_sum = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        losses_sum = abs(trades_df[trades_df['pnl'] <= 0]['pnl'].sum())
        summary['profit_factor'] = wins_sum / losses_sum if losses_sum > 0 else 0

        return summary

    def print_summary(self, days: int = 30, strategy: Optional[str] = None):
        """
        Print formatted summary.

        Args:
            days: Number of days
            strategy: Filter by strategy
        """
        summary = self.get_summary(strategy=strategy, days=days)

        if 'message' in summary:
            print(summary['message'])
            return

        print("\n" + "="*70)
        print(f"TRADE JOURNAL SUMMARY - Last {days} Days")
        if strategy:
            print(f"Strategy: {strategy}")
        print("="*70 + "\n")

        print(f"Total Trades:        {summary['total_trades']}")
        print(f"Winning Trades:      {summary['winning_trades']}")
        print(f"Losing Trades:       {summary['losing_trades']}")
        print(f"Win Rate:            {summary['win_rate']:.2f}%")
        print(f"\nTotal P&L:           ${summary['total_pnl']:.2f}")
        print(f"Avg P&L:             {summary['total_pnl_pct']:.2f}%")
        print(f"Avg Win:             {summary['avg_win']:.2f}%")
        print(f"Avg Loss:            {summary['avg_loss']:.2f}%")
        print(f"Profit Factor:       {summary['profit_factor']:.2f}")
        print(f"\nBest Trade:          {summary['best_trade']:.2f}%")
        print(f"Worst Trade:         {summary['worst_trade']:.2f}%")
        print(f"Avg Duration:        {summary['avg_duration_hours']:.1f}h")
        print("\n" + "="*70 + "\n")

    def export_all(self, output_dir: str = "exports"):
        """
        Export all data to CSV files.

        Args:
            output_dir: Output directory
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Export signals
        self.db.export_to_csv(
            'signals',
            f"{output_dir}/signals_{timestamp}.csv"
        )

        # Export trades
        self.db.export_to_csv(
            'trades',
            f"{output_dir}/trades_{timestamp}.csv"
        )

        # Export daily performance
        self.db.export_to_csv(
            'daily_performance',
            f"{output_dir}/daily_performance_{timestamp}.csv"
        )

        print(f"\n✓ All data exported to {output_dir}/")

    def close(self):
        """Close database connection."""
        self.db.close()
