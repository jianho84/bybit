"""
Configuration Management for Crypto Quant Trading System
=========================================================
Centralized configuration using Pydantic for type safety and validation.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class Exchange(str, Enum):
    """Supported exchanges."""
    BYBIT = "bybit"
    BINANCE = "binance"
    OKX = "okx"
    DERIBIT = "deribit"


class StrategyType(str, Enum):
    """Available strategy types."""
    LIQUIDITY_IMBALANCE = "liquidity_imbalance_mean_reversion"
    VOLATILITY_BREAKOUT = "volatility_normalization_breakout"
    SPOT_PERP_BASIS = "spot_perp_basis_arbitrage"
    DYNAMIC_FUNDING = "dynamic_funding_rate_arbitrage"


class ExchangeConfig(BaseModel):
    """Exchange connection configuration."""

    name: Exchange = Exchange.BYBIT
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    testnet: bool = True
    rate_limit: int = 100  # requests per minute

    # WebSocket settings
    enable_websocket: bool = True
    ws_reconnect_delay: int = 5

    # Data settings
    ohlcv_limit: int = 1000
    trade_limit: int = 500


class RiskConfig(BaseModel):
    """Risk management parameters."""

    # Portfolio risk
    max_portfolio_risk: float = Field(0.02, description="Max 2% portfolio risk per trade")
    max_position_size: float = Field(0.25, description="Max 25% of portfolio per position")
    max_leverage: float = Field(5.0, description="Maximum leverage allowed")

    # Stop-loss settings
    default_stop_loss_pct: float = Field(0.015, description="Default 1.5% stop loss")
    max_stop_loss_pct: float = Field(0.05, description="Maximum 5% stop loss")

    # Position limits
    max_open_positions: int = Field(5, description="Max concurrent positions")
    max_correlated_positions: int = Field(2, description="Max correlated asset positions")

    # Drawdown controls
    max_daily_drawdown: float = Field(0.05, description="Max 5% daily drawdown")
    max_weekly_drawdown: float = Field(0.10, description="Max 10% weekly drawdown")
    max_monthly_drawdown: float = Field(0.15, description="Max 15% monthly drawdown")

    # Kelly Criterion
    use_kelly_sizing: bool = True
    kelly_fraction: float = Field(0.25, description="Use 1/4 Kelly for safety")

    # Correlation limits
    max_correlation_threshold: float = Field(0.7, description="Max 0.7 correlation between positions")


class StrategyConfig(BaseModel):
    """Strategy-specific configuration."""

    strategy_type: StrategyType
    enabled: bool = True

    # Asset universe
    assets: List[str] = Field(
        default=["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT"],
        description="Trading pairs"
    )

    # Timeframe
    timeframe: str = Field("5m", description="OHLCV timeframe")

    # Performance targets
    min_sharpe_ratio: float = Field(1.5, description="Minimum acceptable Sharpe")
    target_annual_return: float = Field(0.40, description="Target 40% annual return")

    # Strategy-specific parameters (override in subclasses)
    params: Dict = Field(default_factory=dict)

    @validator('assets')
    def validate_assets(cls, v):
        """Ensure asset list is not empty."""
        if not v:
            raise ValueError("Asset list cannot be empty")
        return v


class LiquidityImbalanceConfig(StrategyConfig):
    """Configuration for Liquidity Imbalance Mean Reversion strategy."""

    strategy_type: StrategyType = StrategyType.LIQUIDITY_IMBALANCE

    class Params(BaseModel):
        # Signal detection
        volume_sigma_threshold: float = Field(4.2, description="Z-score for large order detection")
        spread_consumption_pct: float = Field(0.80, description="% of spread consumed")
        lookback_periods: int = Field(100, description="Periods for rolling statistics")

        # Entry confirmation
        rsi_period: int = Field(6, description="RSI period for confirmation")
        rsi_oversold: float = Field(30, description="RSI oversold threshold")
        rsi_overbought: float = Field(70, description="RSI overbought threshold")

        # Exit parameters
        profit_target_pct: float = Field(0.0025, description="0.25% profit target")
        stop_loss_pct: float = Field(0.0015, description="0.15% stop loss")
        max_holding_periods: int = Field(12, description="Max 1 hour holding (12x5m)")

        # Risk controls
        max_trade_risk_pct: float = Field(0.005, description="0.5% risk per trade")
        min_liquidity_usd: float = Field(1_000_000, description="Min $1M liquidity")

    params: Params = Field(default_factory=Params)


class VolatilityBreakoutConfig(StrategyConfig):
    """Configuration for Volatility Normalization Breakout strategy."""

    strategy_type: StrategyType = StrategyType.VOLATILITY_BREAKOUT

    class Params(BaseModel):
        # Bollinger Bands
        bb_period: int = Field(20, description="Bollinger Band period")
        bb_std: float = Field(2.0, description="Bollinger Band standard deviations")

        # Volatility compression
        bandwidth_percentile: float = Field(20, description="Bandwidth compression percentile")
        bandwidth_lookback: int = Field(90, description="90-day lookback for percentile")

        # Volume confirmation
        volume_ma_period: int = Field(20, description="Volume MA period")
        volume_threshold: float = Field(1.2, description="Volume must be 1.2x average")

        # Exit parameters
        use_trailing_stop: bool = True
        chandelier_atr_multiple: float = Field(3.0, description="3x ATR for Chandelier exit")
        atr_period: int = Field(14, description="ATR calculation period")

        # Risk controls
        min_volatility_regime: bool = True  # Only trade in low->high vol transitions
        max_atr_position_size: bool = True  # Scale position by ATR

    params: Params = Field(default_factory=Params)


class SpotPerpBasisConfig(StrategyConfig):
    """Configuration for Spot-Perpetual Basis Funding Arbitrage."""

    strategy_type: StrategyType = StrategyType.SPOT_PERP_BASIS

    class Params(BaseModel):
        # Funding rate parameters
        min_funding_rate: float = Field(0.0005, description="Min 0.05% funding rate")
        funding_interval_hours: int = Field(8, description="Funding interval")

        # Basis calculation
        min_basis_bps: float = Field(10, description="Min 10 bps basis spread")
        basis_persistence_periods: int = Field(3, description="Basis must persist N periods")

        # Entry/Exit
        entry_threshold_annualized: float = Field(0.15, description="15% annualized return threshold")
        exit_threshold_pct: float = Field(0.70, description="Exit at 70% of entry threshold")

        # Hedging
        hedge_ratio: float = Field(1.0, description="Delta-neutral hedge ratio")
        rehedge_threshold: float = Field(0.02, description="Rehedge at 2% delta drift")

        # Risk controls
        max_basis_risk: float = Field(0.01, description="Max 1% basis convergence risk")
        monitor_funding_flip: bool = True  # Exit if funding flips sign

    params: Params = Field(default_factory=Params)


class DynamicFundingConfig(StrategyConfig):
    """Configuration for Dynamic Funding Rate Cycle Arbitrage."""

    strategy_type: StrategyType = StrategyType.DYNAMIC_FUNDING

    class Params(BaseModel):
        # Funding cycle analysis
        funding_lookback_days: int = Field(30, description="Historical funding analysis period")
        cycle_detection_method: str = Field("fft", description="FFT for cycle detection")

        # Dynamic thresholds
        funding_percentile_entry: float = Field(80, description="Enter at 80th percentile")
        funding_percentile_exit: float = Field(50, description="Exit at 50th percentile")

        # Position adjustment
        dynamic_hedge_ratio: bool = True
        hedge_ratio_range: tuple = Field((0.8, 1.2), description="Hedge ratio bounds")

        # Timing optimization
        optimal_entry_hours: List[int] = Field(
            default=[0, 8, 16],
            description="Hours before funding payment"
        )

        # Yield enhancement
        compound_funding: bool = True
        min_compounding_threshold: float = Field(0.01, description="Min 1% for rebalancing")

        # Risk controls
        max_funding_volatility: float = Field(0.02, description="Max 2% funding volatility")
        correlation_filter: bool = True  # Filter for funding rate mean reversion

    params: Params = Field(default_factory=Params)


class BacktestConfig(BaseModel):
    """Backtesting configuration."""

    start_date: str = "2023-01-01"
    end_date: str = "2024-12-31"
    initial_capital: float = 100_000.0

    # Slippage and fees
    maker_fee: float = 0.0002  # 0.02%
    taker_fee: float = 0.0006  # 0.06%
    slippage_bps: float = 2.0  # 2 bps slippage

    # Execution simulation
    simulate_latency: bool = True
    latency_ms: int = 50
    fill_probability: float = 0.98  # 98% fill rate for limit orders

    # Performance metrics
    calculate_sharpe: bool = True
    calculate_sortino: bool = True
    calculate_max_drawdown: bool = True
    calculate_var: bool = True  # Value at Risk
    var_confidence: float = 0.95


class Config(BaseModel):
    """Master configuration."""

    # Environment
    environment: str = Field("development", description="development/staging/production")

    # Components
    exchange: ExchangeConfig = Field(default_factory=ExchangeConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)

    # Strategies (can enable multiple)
    strategies: List[StrategyConfig] = Field(default_factory=list)

    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_dir: str = "logs"

    # Notifications
    enable_telegram: bool = False
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Database
    use_database: bool = True
    database_path: str = "data/trading.db"

    # Performance monitoring
    performance_check_interval: int = 3600  # Check every hour
    auto_shutdown_on_drawdown: bool = True

    class Config:
        """Pydantic config."""
        use_enum_values = True


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from file or return default.

    Args:
        config_path: Path to JSON config file

    Returns:
        Config instance
    """
    if config_path:
        import json
        with open(config_path, 'r') as f:
            data = json.load(f)
        return Config(**data)

    # Return default config with all strategies
    return Config(
        strategies=[
            LiquidityImbalanceConfig(),
            VolatilityBreakoutConfig(),
            SpotPerpBasisConfig(),
            DynamicFundingConfig(),
        ]
    )
