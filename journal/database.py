"""
Trade Database Module
====================
SQLite database for persistent trade and signal storage.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


class TradeDatabase:
    """
    SQLite database for trade journaling.

    Stores:
    - Signals: All generated trading signals
    - Trades: Executed trades with actual fills
    - Performance: Daily/monthly statistics
    """

    def __init__(self, db_path: str = "data/trading_journal.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries

        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Signals table - stores all generated signals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                strategy TEXT NOT NULL,
                asset TEXT NOT NULL,
                timeframe TEXT,
                direction TEXT NOT NULL,

                -- Price levels
                entry_price REAL NOT NULL,
                entry_zone_min REAL,
                entry_zone_max REAL,
                stop_loss REAL NOT NULL,
                take_profit REAL,

                -- Position sizing
                position_size_usd REAL,
                position_size_units REAL,
                position_size_pct REAL,
                risk_pct REAL,
                leverage REAL,

                -- Signal quality
                confidence REAL,
                expected_win_rate REAL,
                expected_profit_factor REAL,

                -- Justification (full text)
                trigger_condition TEXT,
                market_state TEXT,
                edge_rationale TEXT,
                risk_assessment TEXT,

                -- Status tracking
                status TEXT DEFAULT 'generated',  -- generated, filled, missed, cancelled
                notes TEXT,

                -- Metadata
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Trades table - stores actual executed trades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id INTEGER,

                -- Trade details
                strategy TEXT NOT NULL,
                asset TEXT NOT NULL,
                direction TEXT NOT NULL,

                -- Entry
                entry_time TEXT NOT NULL,
                entry_price REAL NOT NULL,
                entry_size_units REAL NOT NULL,
                entry_size_usd REAL NOT NULL,
                entry_fee REAL,

                -- Exit
                exit_time TEXT,
                exit_price REAL,
                exit_reason TEXT,  -- stop_loss, take_profit, trailing_stop, manual, time_exit
                exit_fee REAL,

                -- Performance
                pnl REAL,
                pnl_pct REAL,
                pnl_after_fees REAL,
                duration_hours REAL,

                -- Position details
                leverage REAL,
                stop_loss REAL,
                take_profit REAL,

                -- Slippage tracking
                entry_slippage_bps REAL,
                exit_slippage_bps REAL,

                -- Notes
                notes TEXT,

                -- Metadata
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (signal_id) REFERENCES signals (signal_id)
            )
        """)

        # Daily performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                strategy TEXT,

                -- P&L
                gross_pnl REAL,
                net_pnl REAL,
                fees REAL,

                -- Trade stats
                num_trades INTEGER,
                num_wins INTEGER,
                num_losses INTEGER,
                win_rate REAL,

                -- Performance
                sharpe_ratio REAL,
                max_drawdown REAL,

                -- Portfolio
                starting_equity REAL,
                ending_equity REAL,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_timestamp
            ON signals(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_strategy
            ON signals(strategy)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_asset
            ON signals(asset)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_entry_time
            ON trades(entry_time)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_strategy
            ON trades(strategy)
        """)

        self.conn.commit()

    def log_signal(self, signal_data: Dict[str, Any]) -> int:
        """
        Log a trading signal to database.

        Args:
            signal_data: Dictionary with signal information

        Returns:
            Signal ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO signals (
                timestamp, strategy, asset, timeframe, direction,
                entry_price, entry_zone_min, entry_zone_max,
                stop_loss, take_profit,
                position_size_usd, position_size_units, position_size_pct,
                risk_pct, leverage,
                confidence, expected_win_rate, expected_profit_factor,
                trigger_condition, market_state, edge_rationale, risk_assessment,
                status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal_data.get('timestamp', datetime.now().isoformat()),
            signal_data.get('strategy', ''),
            signal_data.get('asset', ''),
            signal_data.get('timeframe', ''),
            signal_data.get('direction', ''),
            signal_data.get('entry_price', 0),
            signal_data.get('entry_zone_min', 0),
            signal_data.get('entry_zone_max', 0),
            signal_data.get('stop_loss', 0),
            signal_data.get('take_profit'),
            signal_data.get('position_size_usd', 0),
            signal_data.get('position_size_units', 0),
            signal_data.get('position_size_pct', 0),
            signal_data.get('risk_pct', 0),
            signal_data.get('leverage', 1.0),
            signal_data.get('confidence', 0),
            signal_data.get('expected_win_rate', 0),
            signal_data.get('expected_profit_factor', 0),
            signal_data.get('trigger_condition', ''),
            signal_data.get('market_state', ''),
            signal_data.get('edge_rationale', ''),
            signal_data.get('risk_assessment', ''),
            signal_data.get('status', 'generated'),
            signal_data.get('notes', '')
        ))

        self.conn.commit()
        return cursor.lastrowid

    def log_trade(self, trade_data: Dict[str, Any]) -> int:
        """
        Log a trade to database.

        Args:
            trade_data: Dictionary with trade information

        Returns:
            Trade ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO trades (
                signal_id, strategy, asset, direction,
                entry_time, entry_price, entry_size_units, entry_size_usd, entry_fee,
                exit_time, exit_price, exit_reason, exit_fee,
                pnl, pnl_pct, pnl_after_fees, duration_hours,
                leverage, stop_loss, take_profit,
                entry_slippage_bps, exit_slippage_bps,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data.get('signal_id'),
            trade_data.get('strategy', ''),
            trade_data.get('asset', ''),
            trade_data.get('direction', ''),
            trade_data.get('entry_time', datetime.now().isoformat()),
            trade_data.get('entry_price', 0),
            trade_data.get('entry_size_units', 0),
            trade_data.get('entry_size_usd', 0),
            trade_data.get('entry_fee', 0),
            trade_data.get('exit_time'),
            trade_data.get('exit_price'),
            trade_data.get('exit_reason', ''),
            trade_data.get('exit_fee', 0),
            trade_data.get('pnl', 0),
            trade_data.get('pnl_pct', 0),
            trade_data.get('pnl_after_fees', 0),
            trade_data.get('duration_hours', 0),
            trade_data.get('leverage', 1.0),
            trade_data.get('stop_loss', 0),
            trade_data.get('take_profit'),
            trade_data.get('entry_slippage_bps', 0),
            trade_data.get('exit_slippage_bps', 0),
            trade_data.get('notes', '')
        ))

        self.conn.commit()
        return cursor.lastrowid

    def update_trade(self, trade_id: int, updates: Dict[str, Any]):
        """Update an existing trade."""
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        set_clause += ", updated_at = ?"

        values = list(updates.values()) + [datetime.now().isoformat(), trade_id]

        cursor = self.conn.cursor()
        cursor.execute(f"""
            UPDATE trades
            SET {set_clause}
            WHERE trade_id = ?
        """, values)

        self.conn.commit()

    def get_signals(
        self,
        strategy: Optional[str] = None,
        asset: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Query signals from database.

        Args:
            strategy: Filter by strategy name
            asset: Filter by asset
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            status: Filter by status

        Returns:
            DataFrame of signals
        """
        query = "SELECT * FROM signals WHERE 1=1"
        params = []

        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)

        if asset:
            query += " AND asset = ?"
            params.append(asset)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY timestamp DESC"

        df = pd.read_sql_query(query, self.conn, params=params)
        return df

    def get_trades(
        self,
        strategy: Optional[str] = None,
        asset: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Query trades from database.

        Args:
            strategy: Filter by strategy name
            asset: Filter by asset
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame of trades
        """
        query = "SELECT * FROM trades WHERE 1=1"
        params = []

        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)

        if asset:
            query += " AND asset = ?"
            params.append(asset)

        if start_date:
            query += " AND entry_time >= ?"
            params.append(start_date)

        if end_date:
            query += " AND entry_time <= ?"
            params.append(end_date)

        query += " ORDER BY entry_time DESC"

        df = pd.read_sql_query(query, self.conn, params=params)

        # Convert timestamps to datetime
        if 'entry_time' in df.columns:
            df['entry_time'] = pd.to_datetime(df['entry_time'])
        if 'exit_time' in df.columns:
            df['exit_time'] = pd.to_datetime(df['exit_time'])

        return df

    def log_daily_performance(self, performance_data: Dict[str, Any]):
        """Log daily performance summary."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO daily_performance (
                date, strategy, gross_pnl, net_pnl, fees,
                num_trades, num_wins, num_losses, win_rate,
                sharpe_ratio, max_drawdown,
                starting_equity, ending_equity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            performance_data.get('date', datetime.now().date().isoformat()),
            performance_data.get('strategy'),
            performance_data.get('gross_pnl', 0),
            performance_data.get('net_pnl', 0),
            performance_data.get('fees', 0),
            performance_data.get('num_trades', 0),
            performance_data.get('num_wins', 0),
            performance_data.get('num_losses', 0),
            performance_data.get('win_rate', 0),
            performance_data.get('sharpe_ratio', 0),
            performance_data.get('max_drawdown', 0),
            performance_data.get('starting_equity', 0),
            performance_data.get('ending_equity', 0)
        ))

        self.conn.commit()

    def get_daily_performance(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Get daily performance summary."""
        query = "SELECT * FROM daily_performance WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC"

        df = pd.read_sql_query(query, self.conn, params=params)

        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        return df

    def export_to_csv(self, table: str, output_path: str):
        """
        Export table to CSV.

        Args:
            table: Table name (signals, trades, daily_performance)
            output_path: Output CSV file path
        """
        df = pd.read_sql_query(f"SELECT * FROM {table}", self.conn)
        df.to_csv(output_path, index=False)
        print(f"Exported {len(df)} rows to {output_path}")

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __del__(self):
        """Ensure connection is closed."""
        if hasattr(self, 'conn'):
            self.conn.close()
