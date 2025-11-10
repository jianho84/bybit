"""
Data Loader Module
==================
Load and prepare market data for backtesting and live trading.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import ccxt


class DataLoader:
    """Load market data from various sources."""

    def __init__(self, exchange_name: str = 'bybit'):
        """
        Initialize data loader.

        Args:
            exchange_name: Name of exchange
        """
        self.exchange_name = exchange_name
        self.exchange = None

    def connect_exchange(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Connect to exchange."""
        exchange_class = getattr(ccxt, self.exchange_name)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

    def load_ohlcv(
        self,
        symbol: str,
        timeframe: str = '5m',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Load OHLCV data.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Number of candles

        Returns:
            DataFrame with OHLCV data
        """
        if self.exchange is None:
            self.connect_exchange()

        # Convert dates to timestamps
        since = None
        if start_date:
            since = int(pd.Timestamp(start_date).timestamp() * 1000)

        # Fetch data
        ohlcv = self.exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            since=since,
            limit=limit
        )

        # Convert to DataFrame
        df = pd.DataFrame(
            ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        # Filter by end date
        if end_date:
            df = df[df.index <= end_date]

        return df

    def generate_synthetic_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str = '5m',
        initial_price: float = 50000.0,
        volatility: float = 0.02
    ) -> pd.DataFrame:
        """
        Generate synthetic OHLCV data for testing.

        Args:
            symbol: Symbol name
            start_date: Start date
            end_date: End date
            timeframe: Timeframe
            initial_price: Starting price
            volatility: Daily volatility

        Returns:
            Synthetic OHLCV DataFrame
        """
        # Generate date range
        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)

        # Determine frequency
        freq_map = {
            '1m': '1T', '5m': '5T', '15m': '15T', '30m': '30T',
            '1h': '1H', '4h': '4H', '1d': '1D'
        }
        freq = freq_map.get(timeframe, '5T')

        dates = pd.date_range(start, end, freq=freq)

        # Generate price using geometric Brownian motion
        n = len(dates)
        dt = 1 / (252 * 24 * 12)  # 5-minute intervals

        # Random returns
        returns = np.random.normal(0, volatility * np.sqrt(dt), n)

        # Price path
        price = initial_price * np.exp(np.cumsum(returns))

        # Generate OHLCV
        df = pd.DataFrame(index=dates)
        df['close'] = price

        # Generate realistic OHLC
        df['open'] = df['close'].shift(1).fillna(initial_price)

        spread = df['close'] * 0.001  # 0.1% spread
        df['high'] = df[['open', 'close']].max(axis=1) + spread
        df['low'] = df[['open', 'close']].min(axis=1) - spread

        # Generate volume (correlated with volatility)
        base_volume = 1000000
        volume_volatility = abs(df['close'].pct_change()) * base_volume * 10
        df['volume'] = base_volume + volume_volatility.fillna(0)

        return df

    def generate_funding_rate_data(
        self,
        dates: pd.DatetimeIndex,
        mean_funding: float = 0.0001,
        volatility: float = 0.0002
    ) -> pd.Series:
        """
        Generate synthetic funding rate data.

        Args:
            dates: Date index
            mean_funding: Mean funding rate
            volatility: Funding rate volatility

        Returns:
            Funding rate series
        """
        n = len(dates)

        # Generate with some autocorrelation
        ar_coef = 0.8
        innovations = np.random.normal(0, volatility, n)

        funding_rates = np.zeros(n)
        funding_rates[0] = mean_funding

        for i in range(1, n):
            funding_rates[i] = (
                ar_coef * funding_rates[i-1] +
                (1 - ar_coef) * mean_funding +
                innovations[i]
            )

        return pd.Series(funding_rates, index=dates)
