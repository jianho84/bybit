"""
Technical Indicators Library
============================
Optimized technical indicators for crypto quant strategies.
All functions are vectorized for performance.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from scipy.stats import zscore


class TechnicalIndicators:
    """
    Collection of technical indicators optimized for crypto trading.
    All methods are static and vectorized for maximum performance.
    """

    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.

        Args:
            prices: Price series
            period: RSI period (default 14)

        Returns:
            RSI values (0-100)
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def bollinger_bands(
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.

        Args:
            prices: Price series
            period: Moving average period
            std_dev: Standard deviation multiplier

        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return upper, middle, lower

    @staticmethod
    def bollinger_bandwidth(
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> pd.Series:
        """
        Calculate Bollinger Band Width (volatility indicator).

        Bandwidth = (Upper Band - Lower Band) / Middle Band

        Args:
            prices: Price series
            period: Moving average period
            std_dev: Standard deviation multiplier

        Returns:
            Bandwidth series
        """
        upper, middle, lower = TechnicalIndicators.bollinger_bands(
            prices, period, std_dev
        )
        bandwidth = (upper - lower) / middle
        return bandwidth

    @staticmethod
    def atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period

        Returns:
            ATR values
        """
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    @staticmethod
    def chandelier_exit(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 22,
        multiplier: float = 3.0
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Chandelier Exit (trailing stop).

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period
            multiplier: ATR multiplier

        Returns:
            Tuple of (long_stop, short_stop)
        """
        atr_val = TechnicalIndicators.atr(high, low, close, period)

        long_stop = high.rolling(window=period).max() - (multiplier * atr_val)
        short_stop = low.rolling(window=period).min() + (multiplier * atr_val)

        return long_stop, short_stop

    @staticmethod
    def volume_profile(
        volume: pd.Series,
        window: int = 100
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Analyze volume profile for large order detection.

        Args:
            volume: Volume series
            window: Lookback window

        Returns:
            Tuple of (mean, std, z_score)
        """
        rolling_mean = volume.rolling(window=window).mean()
        rolling_std = volume.rolling(window=window).std()
        z_score = (volume - rolling_mean) / rolling_std

        return rolling_mean, rolling_std, z_score

    @staticmethod
    def detect_large_orders(
        df: pd.DataFrame,
        volume_col: str = 'volume',
        price_col: str = 'close',
        window: int = 100,
        sigma_threshold: float = 4.0
    ) -> pd.DataFrame:
        """
        Detect abnormally large market orders.

        Args:
            df: OHLCV dataframe
            volume_col: Volume column name
            price_col: Price column name
            window: Lookback window for statistics
            sigma_threshold: Z-score threshold for detection

        Returns:
            DataFrame with large order signals
        """
        # Calculate volume statistics
        _, _, z_score = TechnicalIndicators.volume_profile(
            df[volume_col], window
        )

        # Calculate price impact (% change)
        price_impact = df[price_col].pct_change().abs()

        # Detect large orders
        df['volume_zscore'] = z_score
        df['price_impact'] = price_impact
        df['large_buy'] = (
            (z_score > sigma_threshold) &
            (df[price_col] > df[price_col].shift())
        )
        df['large_sell'] = (
            (z_score > sigma_threshold) &
            (df[price_col] < df[price_col].shift())
        )

        return df

    @staticmethod
    def calculate_spread(
        bid: pd.Series,
        ask: pd.Series
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate bid-ask spread metrics.

        Args:
            bid: Bid prices
            ask: Ask prices

        Returns:
            Tuple of (spread_absolute, spread_percentage)
        """
        spread_abs = ask - bid
        spread_pct = (spread_abs / ((bid + ask) / 2)) * 100

        return spread_abs, spread_pct

    @staticmethod
    def ema(prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average.

        Args:
            prices: Price series
            period: EMA period

        Returns:
            EMA values
        """
        return prices.ewm(span=period, adjust=False).mean()

    @staticmethod
    def macd(
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD indicator.

        Args:
            prices: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        ema_fast = TechnicalIndicators.ema(prices, fast)
        ema_slow = TechnicalIndicators.ema(prices, slow)

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
        smooth_k: int = 3,
        smooth_d: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Lookback period
            smooth_k: %K smoothing period
            smooth_d: %D smoothing period

        Returns:
            Tuple of (%K, %D)
        """
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()

        k_raw = 100 * (close - lowest_low) / (highest_high - lowest_low)
        k = k_raw.rolling(window=smooth_k).mean()
        d = k.rolling(window=smooth_d).mean()

        return k, d

    @staticmethod
    def vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series
    ) -> pd.Series:
        """
        Calculate Volume Weighted Average Price.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume

        Returns:
            VWAP values
        """
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()

        return vwap

    @staticmethod
    def rolling_percentile(
        series: pd.Series,
        window: int,
        percentile: float
    ) -> pd.Series:
        """
        Calculate rolling percentile.

        Args:
            series: Data series
            window: Rolling window size
            percentile: Percentile to calculate (0-100)

        Returns:
            Rolling percentile values
        """
        return series.rolling(window=window).quantile(percentile / 100)

    @staticmethod
    def is_volatility_compression(
        prices: pd.Series,
        bb_period: int = 20,
        lookback: int = 90,
        percentile_threshold: float = 20
    ) -> pd.Series:
        """
        Detect volatility compression using Bollinger Bandwidth percentile.

        Args:
            prices: Price series
            bb_period: Bollinger Band period
            lookback: Historical lookback for percentile
            percentile_threshold: Threshold for compression (default 20th percentile)

        Returns:
            Boolean series indicating compression
        """
        bandwidth = TechnicalIndicators.bollinger_bandwidth(prices, bb_period)
        percentile_level = TechnicalIndicators.rolling_percentile(
            bandwidth, lookback, percentile_threshold
        )

        is_compressed = bandwidth <= percentile_level

        return is_compressed

    @staticmethod
    def detect_breakout(
        df: pd.DataFrame,
        price_col: str = 'close',
        volume_col: str = 'volume',
        bb_period: int = 20,
        bb_std: float = 2.0,
        volume_threshold: float = 1.2
    ) -> pd.DataFrame:
        """
        Detect breakout conditions with volume confirmation.

        Args:
            df: OHLCV dataframe
            price_col: Price column name
            volume_col: Volume column name
            bb_period: Bollinger Band period
            bb_std: Bollinger Band std dev
            volume_threshold: Volume multiplier threshold

        Returns:
            DataFrame with breakout signals
        """
        prices = df[price_col]
        upper, middle, lower = TechnicalIndicators.bollinger_bands(
            prices, bb_period, bb_std
        )

        # Volume confirmation
        volume_ma = df[volume_col].rolling(window=bb_period).mean()
        volume_above_avg = df[volume_col] > (volume_ma * volume_threshold)

        # Breakout detection
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower

        df['breakout_long'] = (
            (prices > upper) &
            volume_above_avg &
            (prices.shift() <= upper.shift())
        )

        df['breakout_short'] = (
            (prices < lower) &
            volume_above_avg &
            (prices.shift() >= lower.shift())
        )

        return df

    @staticmethod
    def calculate_returns(prices: pd.Series, periods: int = 1) -> pd.Series:
        """
        Calculate returns.

        Args:
            prices: Price series
            periods: Number of periods for return calculation

        Returns:
            Returns series
        """
        return prices.pct_change(periods=periods)

    @staticmethod
    def rolling_sharpe(
        returns: pd.Series,
        window: int = 252,
        risk_free_rate: float = 0.0
    ) -> pd.Series:
        """
        Calculate rolling Sharpe ratio.

        Args:
            returns: Returns series
            window: Rolling window
            risk_free_rate: Risk-free rate (annualized)

        Returns:
            Rolling Sharpe ratio
        """
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free
        rolling_mean = excess_returns.rolling(window=window).mean()
        rolling_std = excess_returns.rolling(window=window).std()

        sharpe = (rolling_mean / rolling_std) * np.sqrt(252)

        return sharpe
